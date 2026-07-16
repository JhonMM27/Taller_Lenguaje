"""
Servicio de dominio: SunatEnvioService.

Caso de uso: envio de comprobantes y notas de credito al OSE/SUNAT.
Orquesta: XmlSigner, OSE, repositorios.
"""
from __future__ import annotations

import base64
import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from typing import Optional, Protocol

from ..entidades.comprobante import (
    ESTADO_ACEPTADO,
    ESTADO_BORRADOR,
    ESTADO_EMITIDO,
    ESTADO_ENVIADO,
    ESTADO_RECHAZADO,
    ESTADO_ERROR_ENVIO,
    Comprobante,
)
from ..entidades.nota_credito import NotaCredito
from ..excepciones import (
    EnvioSunatFallido,
    ComprobanteRechazado,
    ErrorTecnicoEnvio,
    EstadoInvalido,
    FirmaDigitalInvalida,
    TicketNoEncontrado,
)
from ..puertos.repositorios import (
    IComprobanteRepository,
    INotaCreditoRepository,
    IUnitOfWork,
)
from ..puertos.sunat import IOSEService, IXmlSigner


class _XmlGenerator(Protocol):
    """Contrato para el generador de XML UBL 2.1."""
    def generar(self, comprobante: Comprobante) -> str: ...
    def generar_nota_credito(self, nota: NotaCredito) -> str: ...


def _validar_firma(xml_bytes: bytes) -> None:
    if b"<ds:Signature" not in xml_bytes and b"<Signature" not in xml_bytes:
        raise FirmaDigitalInvalida("El XML NO contiene firma digital (ds:Signature)")
    if b"<ds:X509Certificate>" not in xml_bytes and b"<X509Certificate>" not in xml_bytes:
        raise FirmaDigitalInvalida("El XML NO contiene certificado X509 en la firma")


def _resultado_cdr(cdr_b64):
    if not cdr_b64:
        return None, ""
    try:
        contenido = base64.b64decode(cdr_b64) if isinstance(cdr_b64, str) else cdr_b64
        with zipfile.ZipFile(BytesIO(contenido)) as archivo:
            nombre = next(n for n in archivo.namelist() if n.lower().endswith(".xml"))
            raiz = ET.fromstring(archivo.read(nombre))
        codigo = raiz.findtext(".//{*}ResponseCode")
        descripcion = raiz.findtext(".//{*}Description") or ""
        return (codigo.strip() if codigo else None), descripcion.strip()
    except (ValueError, KeyError, StopIteration, zipfile.BadZipFile, ET.ParseError):
        return None, ""


class SunatEnvioService:
    """Caso de uso: envio SUNAT/OSE."""

    def __init__(
        self,
        uow: IUnitOfWork,
        ose: IOSEService,
        signer: IXmlSigner,
        xml_generator: _XmlGenerator,
        zip_nombre_fn,
        zip_crear_fn,
    ) -> None:
        self._uow = uow
        self._ose = ose
        self._signer = signer
        self._xml = xml_generator
        self._zip_nombre = zip_nombre_fn
        self._zip_crear = zip_crear_fn

    def enviar_comprobante(self, comprobante_id: int) -> dict:
        """Envia un comprobante al OSE. Devuelve dict con resultado."""
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)

        if comprobante.estado not in (
            ESTADO_EMITIDO, ESTADO_ERROR_ENVIO, ESTADO_BORRADOR,
        ):
            raise EstadoInvalido(
                f"No se puede enviar comprobante en estado {comprobante.estado}"
            )

        # 1) Generar XML
        xml = self._xml.generar(comprobante)
        # 2) Firmar
        firmado = self._signer.firmar(xml, comprobante.empresa_id)
        # 3) Validar firma
        xml_bytes = firmado.encode("utf-8") if isinstance(firmado, str) else firmado
        _validar_firma(xml_bytes)
        # 4) Empaquetar
        nombre_zip = self._zip_nombre(comprobante).replace(".zip", "")
        zip_bytes = self._zip_crear(xml_bytes, nombre_zip)
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        # 5) Enviar
        respuesta = self._ose.send_bill(zip_b64, nombre_zip + ".zip")

        if respuesta.get("status") == 0 and respuesta.get("applicationResponse"):
            codigo_cdr, descripcion_cdr = _resultado_cdr(
                respuesta.get("applicationResponse")
            )
            if codigo_cdr and codigo_cdr != "0":
                respuesta["status"] = 99
                respuesta["faultcode"] = codigo_cdr
                respuesta["faultstring"] = (
                    descripcion_cdr or "Comprobante rechazado segun CDR"
                )

        comprobante.xml_firmado = (
            firmado.decode("utf-8") if isinstance(firmado, bytes) else firmado
        )

        if respuesta.get("status") == 0:
            cdr_b64 = respuesta.get("applicationResponse", "")
            comprobante.sunat_ticket = respuesta.get("ticket") or None
            comprobante.estado = ESTADO_ACEPTADO
            with self._uow:
                self._uow.comprobantes.guardar(comprobante)
                self._uow.logs_sunat.registrar(
                    comprobante,
                    estado_respuesta="ACEPTADO",
                    codigo_respuesta="0",
                    descripcion="CDR recibido - Comprobante aceptado por SUNAT/OSE",
                    uuid=respuesta.get("ticket", ""),
                    cdr_xml=cdr_b64,
                )
                self._uow.commit()
            return {
                "success": True,
                "estado": ESTADO_ACEPTADO,
                "ticket": comprobante.sunat_ticket,
                "cdr": bool(cdr_b64),
            }
        else:
            motivo = respuesta.get("faultstring") or "Error al enviar al OSE/SUNAT"
            texto_codigo = ' '.join(str(respuesta.get(k) or '') for k in (
                'faultcode', 'faultstring', 'status'
            ))
            encontrados = re.findall(r'(?<!\d)(\d{4})(?!\d)', texto_codigo)
            codigo = encontrados[0] if encontrados else str(respuesta.get("status", "-1"))
            try:
                es_rechazo = 2000 <= int(codigo) <= 3999
            except (TypeError, ValueError):
                es_rechazo = False
            comprobante.estado = ESTADO_RECHAZADO if es_rechazo else ESTADO_ERROR_ENVIO
            with self._uow:
                self._uow.comprobantes.guardar(comprobante)
                self._uow.logs_sunat.registrar(
                    comprobante,
                    estado_respuesta=comprobante.estado,
                    codigo_respuesta=codigo,
                    descripcion=motivo,
                    cdr_xml=respuesta.get("applicationResponse", "") or "",
                )
                self._uow.commit()
            if es_rechazo:
                raise ComprobanteRechazado(motivo)
            raise ErrorTecnicoEnvio(motivo)

    def enviar_nota_credito(self, nota_id: int) -> dict:
        """Envia una NC al OSE."""
        nota = self._uow.notas_credito.obtener_por_id(nota_id)

        if nota.estado not in (ESTADO_EMITIDO, ESTADO_RECHAZADO, ESTADO_BORRADOR):
            raise EstadoInvalido(
                f"No se puede enviar NC en estado {nota.estado}"
            )

        comprobante_ref = self._uow.comprobantes.obtener_por_id(
            nota.comprobante_referencia_id
        )

        xml = self._xml.generar_nota_credito(nota)
        firmado = self._signer.firmar(xml, comprobante_ref.empresa_id)
        xml_bytes = firmado.encode("utf-8") if isinstance(firmado, str) else firmado
        _validar_firma(xml_bytes)
        nombre_zip = f"RUC-{comprobante_ref.empresa_id}-07-{nota.serie}-{nota.numero:08d}"
        zip_bytes = self._zip_crear(xml_bytes, nombre_zip)
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        respuesta = self._ose.send_bill(zip_b64, nombre_zip + ".zip")

        nota.xml_firmado = (
            firmado.decode("utf-8") if isinstance(firmado, bytes) else firmado
        )

        if respuesta.get("status") == 0:
            nota.cdr_xml = respuesta.get("applicationResponse", "")
            nota.sunat_ticket = respuesta.get("ticket") or None
            nota.estado = ESTADO_ACEPTADO
            nota.mensaje_sunat = "Aceptada por SUNAT"
            with self._uow:
                self._uow.notas_credito.guardar(nota)
                self._uow.commit()
            return {"success": True, "estado": ESTADO_ACEPTADO}
        else:
            nota.estado = ESTADO_RECHAZADO
            nota.mensaje_sunat = (
                respuesta.get("faultstring") or "Rechazada por SUNAT"
            )
            with self._uow:
                self._uow.notas_credito.guardar(nota)
                self._uow.commit()
            raise EnvioSunatFallido(nota.mensaje_sunat)

    def consultar_ticket(self, comprobante_id: int) -> dict:
        """Consulta el estado de un ticket."""
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        if not comprobante.sunat_ticket:
            raise TicketNoEncontrado(
                "No existe ticket para este comprobante"
            )
        respuesta = self._ose.get_status(comprobante.sunat_ticket)
        return {
            "ticket": comprobante.sunat_ticket,
            "status": respuesta.get("status"),
            "descripcion": respuesta.get("faultstring") or "OK",
        }
