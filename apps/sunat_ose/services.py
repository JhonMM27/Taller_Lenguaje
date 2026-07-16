"""
Service Layer para el módulo de envío a SUNAT/OSE.

Toda la lógica de negocio de envío, firma, empaquetado y consulta de tickets.
"""

from dominio.excepciones import RecursoNoEncontrado
import base64
import logging
import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import date

from django.conf import settings
from django.db import transaction

from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from apps.sunat_ose.models import LoteEnvio
from apps.core.exceptions import (
    ComprobanteNoEncontrado,
    EstadoInvalido,
    FirmaDigitalInvalida,
    EnvioSunatFallido,
    ComprobanteRechazado,
    ErrorTecnicoEnvio,
    TicketNoEncontrado,
)

logger = logging.getLogger(__name__)


def _codigo_sunat(respuesta):
    """Extrae el codigo SUNAT aunque venga dentro de un SOAP Fault."""
    texto = ' '.join(str(respuesta.get(k) or '') for k in (
        'faultcode', 'faultstring', 'status'
    ))
    codigos = re.findall(r'(?<!\d)(\d{4})(?!\d)', texto)
    return codigos[0] if codigos else str(respuesta.get('status', '-1'))


def _es_rechazo_sunat(codigo):
    try:
        return 2000 <= int(codigo) <= 3999
    except (TypeError, ValueError):
        return False


def _leer_resultado_cdr(cdr_b64):
    """Devuelve (codigo, descripcion) desde el ZIP CDR, o (None, '')."""
    if not cdr_b64:
        return None, ''
    try:
        contenido = base64.b64decode(cdr_b64) if isinstance(cdr_b64, str) else cdr_b64
        with zipfile.ZipFile(BytesIO(contenido)) as archivo:
            nombre_xml = next(n for n in archivo.namelist() if n.lower().endswith('.xml'))
            raiz = ET.fromstring(archivo.read(nombre_xml))
        codigo = raiz.findtext('.//{*}ResponseCode')
        descripcion = raiz.findtext('.//{*}Description') or ''
        return (codigo.strip() if codigo else None), descripcion.strip()
    except (ValueError, KeyError, StopIteration, zipfile.BadZipFile, ET.ParseError):
        logger.warning('No se pudo interpretar el CDR recibido', exc_info=True)
        return None, ''


def _validar_xml_firmado(xml_content) -> None:
    """Valida que el XML contenga firma digital. Lanza FirmaDigitalInvalida si no."""
    xml_bytes = xml_content if isinstance(xml_content, bytes) else xml_content.encode('utf-8')
    if b'<ds:Signature' not in xml_bytes and b'<Signature' not in xml_bytes:
        raise FirmaDigitalInvalida("El XML NO contiene firma digital (ds:Signature)")
    if b'<ds:X509Certificate>' not in xml_bytes and b'<X509Certificate>' not in xml_bytes:
        raise FirmaDigitalInvalida("El XML NO contiene certificado X509 en la firma")


class SunatEnvioService:
    """Lógica de negocio para envío de comprobantes a SUNAT/OSE."""

    @staticmethod
    def enviar(comprobante_id: int) -> dict:
        """
        Envía un comprobante individual al OSE (Mock o Real).

        Flujo SUNAT sendBill:
        1. Generar XML UBL 2.1
        2. Firmar XML digitalmente
        3. Validar firma
        4. Empaquetar en ZIP
        5. Enviar vía sendBill
        6. Procesar respuesta (ACEPTADO/RECHAZADO)

        Returns:
            dict con success, estado, mensaje, ticket, etc.

        Raises:
            ComprobanteNoEncontrado, EstadoInvalido, FirmaDigitalInvalida, EnvioSunatFallido
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        from apps.sunat_ose.repositories import LogSunatRepositoryDjango

        comprobante_repo = ComprobanteRepositoryDjango()
        log_repo = LogSunatRepositoryDjango()

        comprobante = comprobante_repo.obtener_por_id(comprobante_id)

        if comprobante.estado not in ['EMITIDO', 'ERROR_ENVIO', 'BORRADOR']:
            raise EstadoInvalido(
                f"No se puede enviar comprobante en estado {comprobante.estado}"
            )

        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        logger.info(f"{'='*60}")
        logger.info(f"ENVIANDO COMPROBANTE {comprobante} - MODO: {'MOCK' if es_mock else 'REAL'}")
        logger.info(f"{'='*60}")

        # 1. Generar XML UBL 2.1
        from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml, crear_zip
        logger.info(f"[PASO 1] Generando XML UBL 2.1")
        xml_content = generar_xml_ubl(comprobante)

        # 2. Firmar XML
        logger.info(f"[PASO 2] Firmando XML digitalmente")
        xml_firmado = firmar_xml(xml_content, empresa_id=comprobante.empresa_id)

        # 3. Validar firma
        logger.info(f"[PASO 3] Validando firma digital")
        _validar_xml_firmado(xml_firmado)

        # 4. Empaquetar en ZIP
        logger.info(f"[PASO 4] Empaquetando en ZIP")
        nombre_zip = comprobante.nombre_zip.replace('.zip', '')
        zip_content = crear_zip(xml_firmado, nombre_zip)
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')

        # 5. Enviar a OSE
        from apps.sunat_ose.ose_client import get_ose_client
        ose_client = get_ose_client()
        file_name = (
            f"{comprobante.empresa.ruc}-{comprobante.tipo}"
            f"-{comprobante.serie.serie}-{comprobante.numero:08d}.zip"
        )

        logger.info(f"[PASO 5] Enviando a {'MOCK' if es_mock else 'SUNAT/OSE REAL'}: {file_name}")
        respuesta = ose_client.send_bill(zip_base64, file_name)

        # sendBill puede responder correctamente a nivel SOAP y adjuntar un CDR
        # rechazado. El ResponseCode del CDR es la fuente de verdad tributaria.
        if respuesta.get('status') == 0 and respuesta.get('applicationResponse'):
            codigo_cdr, descripcion_cdr = _leer_resultado_cdr(
                respuesta.get('applicationResponse')
            )
            if codigo_cdr and codigo_cdr != '0':
                respuesta['status'] = 99
                respuesta['faultcode'] = codigo_cdr
                respuesta['faultstring'] = descripcion_cdr or 'Comprobante rechazado segun CDR'

        # 6. Guardar XML firmado
        comprobante.xml_firmado = (
            xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        )

        # 7. Procesar respuesta
        if respuesta.get('status') == 0:
            cdr_b64 = respuesta.get('applicationResponse', '')

            log_repo.registrar_envio(
                comprobante=comprobante,
                estado_respuesta='ACEPTADO',
                codigo_respuesta='0',
                descripcion='CDR recibido - Comprobante aceptado por SUNAT/OSE',
                uuid=respuesta.get('ticket', ''),
                cdr_xml=cdr_b64,
            )

            comprobante.sunat_ticket = respuesta.get('ticket') or None
            comprobante.estado = 'ACEPTADO'
            comprobante_repo.guardar(comprobante)

            logger.info(f"COMPROBANTE {comprobante} ACEPTADO")

            return {
                'success': True,
                'message': 'Comprobante aceptado por SUNAT',
                'ticket': comprobante.sunat_ticket,
                'estado': 'ACEPTADO',
                'cdr': bool(cdr_b64),
                'es_mock': es_mock,
            }
        else:
            codigo = _codigo_sunat(respuesta)
            es_rechazo = _es_rechazo_sunat(codigo)
            estado = 'RECHAZADO' if es_rechazo else 'ERROR_ENVIO'
            descripcion = respuesta.get('faultstring') or 'Error al enviar al OSE/SUNAT'
            log_repo.registrar_envio(
                comprobante=comprobante,
                estado_respuesta=estado,
                codigo_respuesta=codigo,
                descripcion=descripcion,
                uuid='',
                cdr_xml=respuesta.get('applicationResponse', '') or '',
            )

            comprobante.estado = estado
            comprobante_repo.guardar(comprobante)

            if es_rechazo:
                logger.warning(f"COMPROBANTE {comprobante} RECHAZADO: {descripcion}")
                raise ComprobanteRechazado(descripcion)
            logger.error(f"ERROR TECNICO ENVIANDO {comprobante}: {descripcion}")
            raise ErrorTecnicoEnvio(descripcion)

            logger.warning(f"COMPROBANTE {comprobante} RECHAZADO: {respuesta.get('faultstring')}")

            raise EnvioSunatFallido(
                respuesta.get('faultstring', 'Error en el envío a SUNAT/OSE')
            )

    @staticmethod
    def consultar_ticket(comprobante_id: int) -> dict:
        """
        Consulta el estado de un ticket en el OSE.

        Raises:
            ComprobanteNoEncontrado, TicketNoEncontrado
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        from apps.sunat_ose.repositories import LogSunatRepositoryDjango

        comprobante_repo = ComprobanteRepositoryDjango()
        log_repo = LogSunatRepositoryDjango()

        comprobante = comprobante_repo.obtener_por_id(comprobante_id)

        if not comprobante.sunat_ticket:
            raise TicketNoEncontrado(
                "No existe ticket para este comprobante"
            )

        from apps.sunat_ose.ose_client import get_ose_client
        ose_client = get_ose_client()

        logger.info(f"Consultando ticket {comprobante.sunat_ticket}")
        respuesta_status = ose_client.get_status(comprobante.sunat_ticket)

        if respuesta_status.get('status') == 0:
            respuesta_cdr = ose_client.get_status_cdr(comprobante.sunat_ticket)

            cdr_raw = respuesta_cdr.get('cdrContent') or respuesta_cdr.get('cdr_content') or b''
            if isinstance(cdr_raw, str):
                cdr_raw = cdr_raw.encode('utf-8')

            cdr_base64 = ''
            if cdr_raw:
                try:
                    cdr_base64 = base64.b64encode(cdr_raw).decode('utf-8')
                except Exception:
                    cdr_base64 = ''

            log_repo.registrar_envio(
                comprobante=comprobante,
                estado_respuesta='ACEPTADO',
                codigo_respuesta='0',
                descripcion='CDR recibido - Comprobante aceptado por SUNAT',
                uuid=comprobante.sunat_ticket,
                cdr_xml=cdr_base64,
            )

            comprobante.estado = 'ACEPTADO'
            comprobante_repo.guardar(comprobante)

            return {
                'success': True,
                'estado': 'ACEPTADO',
                'descripcion': 'Comprobante aceptado por SUNAT',
                'ticket': comprobante.sunat_ticket,
            }
        elif respuesta_status.get('status') == 99:
            comprobante.estado = 'RECHAZADO'
            comprobante.save(update_fields=['estado'])

            raise EnvioSunatFallido(
                respuesta_status.get('faultstring', 'Rechazado por SUNAT')
            )
        else:
            return {
                'success': True,
                'estado': 'PROCESANDO',
                'descripcion': 'El comprobante aún está siendo procesado',
                'ticket': comprobante.sunat_ticket,
            }

    @staticmethod
    def enviar_lote(comprobante_ids: list, usuario=None) -> LoteEnvio:
        """
        Envía un conjunto de comprobantes individualmente uno por uno a la SUNAT/OSE (sendBill)
        para asegurar compatibilidad con facturas y boletas de forma síncrona.
        """
        comprobantes = Comprobante.objects.filter(
            id__in=comprobante_ids,
            estado__in=['EMITIDO', 'BORRADOR', 'ERROR_ENVIO']
        ).select_related('empresa')

        if not comprobantes.exists():
            raise EstadoInvalido("No se encontraron comprobantes válidos para enviar")

        empresa = comprobantes.first().empresa
        fecha_emision = date.today()

        # Crear registro de Lote
        lote = LoteEnvio.objects.create(
            empresa=empresa,
            fecha_emision_documentos=fecha_emision,
            total_documentos=comprobantes.count(),
            estado='PROCESANDO',
            ticket_ose='PROCESADO_EN_BLOQUE',
            observacion='Procesando envío en bloque...',
            creado_por=usuario,
        )

        exitos = 0
        fallas = 0
        ultimo_error = ""
        ids_exitosos = []

        # Enviar cada comprobante individualmente
        for comprobante in comprobantes:
            try:
                # El método enviar ya cambia el estado del comprobante a ACEPTADO o RECHAZADO
                # y registra los logs de la SUNAT/OSE correspondientes.
                resultado = SunatEnvioService.enviar(comprobante.id)
                if resultado.get('success'):
                    exitos += 1
                    ids_exitosos.append(str(comprobante.id))
                else:
                    fallas += 1
            except Exception as e:
                fallas += 1
                ultimo_error = str(e)
                logger.error(f"Error enviando comprobante {comprobante.id} en lote: {ultimo_error}")

        # Guardar IDs de comprobantes exitosos en ticket_ose para poder
        # recuperarlos después (ej: descarga de CDRs del lote)
        lote.ticket_ose = ','.join(ids_exitosos) if ids_exitosos else 'NONE'

        # Finalizar estado del lote
        if exitos == comprobantes.count():
            lote.estado = 'COMPLETADO'
            lote.observacion = f"Lote procesado. Éxitos: {exitos}, Fallas: {fallas}"
        elif exitos > 0:
            lote.estado = 'COMPLETADO'
            lote.observacion = f"Lote parcial. Éxitos: {exitos}, Fallas: {fallas}. Último error: {ultimo_error}"
        else:
            lote.estado = 'ERROR'
            lote.observacion = f"Lote fallido. Éxitos: {exitos}, Fallas: {fallas}. Último error: {ultimo_error}"
            lote.save()
            raise EnvioSunatFallido(lote.observacion)

        lote.save()
        return lote

    @staticmethod
    def enviar_nota_credito(nota_id: int) -> dict:
        """
        Envía una nota de crédito individual al OSE/SUNAT (Mock o Real).
        """
        from apps.notas_credito.models import NotaCredito
        try:
            nota = NotaCredito.objects.select_related('comprobante_referencia', 'comprobante_referencia__empresa').get(id=nota_id)
        except NotaCredito.DoesNotExist:
            raise RecursoNoEncontrado(f"No existe nota de crédito con id={nota_id}")

        if nota.estado not in ['EMITIDO', 'RECHAZADO', 'BORRADOR']:
            raise EstadoInvalido(f"No se puede enviar nota de crédito en estado {nota.estado}")

        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        logger.info(f"{'='*60}")
        logger.info(f"ENVIANDO NOTA DE CREDITO {nota} - MODO: {'MOCK' if es_mock else 'REAL'}")
        logger.info(f"{'='*60}")

        # 1. Generar XML UBL 2.1
        from apps.sunat_ose.xml_generator import generar_xml_nota_credito, firmar_xml, crear_zip
        logger.info(f"[PASO 1] Generando XML UBL 2.1 para Nota de Crédito")
        xml_content = generar_xml_nota_credito(nota)

        # 2. Firmar XML
        logger.info(f"[PASO 2] Firmando XML digitalmente")
        xml_firmado = firmar_xml(xml_content, empresa_id=nota.comprobante_referencia.empresa_id)

        # 3. Validar firma
        logger.info(f"[PASO 3] Validando firma digital")
        _validar_xml_firmado(xml_firmado)

        # 4. Empaquetar en ZIP
        logger.info(f"[PASO 4] Empaquetando en ZIP")
        nombre_zip = f"{nota.comprobante_referencia.empresa.ruc}-07-{nota.serie}-{nota.numero:08d}"
        zip_content = crear_zip(xml_firmado, nombre_zip)
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')

        # 5. Enviar a OSE
        from apps.sunat_ose.ose_client import get_ose_client
        ose_client = get_ose_client()
        file_name = nombre_zip + ".zip"

        logger.info(f"[PASO 5] Enviando a {'MOCK' if es_mock else 'SUNAT/OSE REAL'}: {file_name}")
        respuesta = ose_client.send_bill(zip_base64, file_name)

        # 6. Guardar XML firmado
        nota.xml_firmado = (
            xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        )

        # 7. Procesar respuesta
        if respuesta.get('status') == 0:
            cdr_b64 = respuesta.get('applicationResponse', '')
            nota.cdr_xml = cdr_b64
            nota.sunat_ticket = respuesta.get('ticket') or None
            nota.estado = 'ACEPTADO'
            nota.mensaje_sunat = 'Aceptada por SUNAT'
            nota.save()

            logger.info(f"NOTA DE CREDITO {nota} ACEPTADA")

            return {
                'success': True,
                'message': 'Nota de crédito aceptada por SUNAT',
                'estado': 'ACEPTADO',
                'cdr': bool(cdr_b64),
                'es_mock': es_mock,
            }
        else:
            nota.estado = 'RECHAZADO'
            nota.mensaje_sunat = respuesta.get('faultstring') or 'Rechazada por SUNAT'
            nota.save()

            logger.warning(f"NOTA DE CREDITO {nota} RECHAZADA: {nota.mensaje_sunat}")

            raise EnvioSunatFallido(nota.mensaje_sunat)

    @staticmethod
    @transaction.atomic
    def consultar_lote(lote_id: int) -> dict:
        """
        Consulta el estado de un lote (LoteEnvio) asíncrono y actualiza todos sus comprobantes.
        """
        try:
            lote = LoteEnvio.objects.get(id=lote_id)
        except LoteEnvio.DoesNotExist:
            raise RecursoNoEncontrado(f"No existe lote con id={lote_id}")

        if not lote.ticket_ose:
            raise TicketNoEncontrado("No existe ticket OSE para este lote")

        from apps.sunat_ose.ose_client import get_ose_client
        ose_client = get_ose_client()

        logger.info(f"Consultando ticket de lote {lote.ticket_ose}")
        respuesta_status = ose_client.get_status(lote.ticket_ose)

        # Si el lote fue procesado con éxito
        if respuesta_status.get('status') == 0:
            # Obtener el CDR del lote
            respuesta_cdr = ose_client.get_status_cdr(lote.ticket_ose)
            cdr_raw = respuesta_cdr.get('cdrContent') or respuesta_cdr.get('cdr_content') or b''
            
            cdr_base64 = ''
            if cdr_raw:
                try:
                    cdr_base64 = base64.b64encode(cdr_raw).decode('utf-8') if isinstance(cdr_raw, bytes) else cdr_raw
                except Exception:
                    cdr_base64 = ''

            # Actualizar estado de los comprobantes asociados a este lote
            comprobantes = Comprobante.objects.filter(sunat_ticket=lote.ticket_ose)
            
            from apps.sunat_ose.repositories import LogSunatRepositoryDjango
            log_repo = LogSunatRepositoryDjango()

            for comprobante in comprobantes:
                comprobante.estado = 'ACEPTADO'
                comprobante.save(update_fields=['estado'])

                log_repo.registrar_envio(
                    comprobante=comprobante,
                    estado_respuesta='ACEPTADO',
                    codigo_respuesta='0',
                    descripcion=f'Lote #{lote.id} procesado y aceptado por SUNAT/OSE',
                    uuid=lote.ticket_ose,
                    cdr_xml=cdr_base64,
                )

            lote.estado = 'COMPLETADO'
            lote.observacion = 'Lote aceptado y comprobantes actualizados'
            lote.save()

            return {
                'success': True,
                'estado': 'COMPLETADO',
                'message': 'Lote procesado exitosamente',
            }
        elif respuesta_status.get('status') == 99 or respuesta_status.get('status') == -1:
            # Lote rechazado
            comprobantes = Comprobante.objects.filter(sunat_ticket=lote.ticket_ose)
            comprobantes.update(estado='RECHAZADO')

            lote.estado = 'ERROR'
            lote.observacion = respuesta_status.get('faultstring') or 'Lote rechazado'
            lote.save()

            raise EnvioSunatFallido(lote.observacion)
        else:
            return {
                'success': True,
                'estado': 'PROCESANDO',
                'message': 'El lote aún está siendo procesado por SUNAT',
            }
