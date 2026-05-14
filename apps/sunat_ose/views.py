from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from apps.sunat_ose.models import LoteEnvio
from .xml_generator import generar_xml_ubl, crear_zip
from .ose_client import get_ose_client
import logging
import base64
import zipfile
from io import BytesIO
from datetime import date

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EnviarComprobanteView(View):
    """
    Vista para enviar un comprobante individual al OSE (Mock o Real).

    Flujo SUNAT para comprobantes individuales (sendBill):
    -------------------------------------------------------
    - sendBill retorna el CDR (Constancia de Recepción) de forma INMEDIATA
      en el campo 'applicationResponse' (base64 del ZIP con el CDR).
    - NO genera ticket asíncrono. El comprobante pasa a ACEPTADO en esta misma llamada.

    Flujo SUNAT para lotes (sendPack) — manejado en enviar_lote():
    ---------------------------------------------------------------
    - sendPack retorna un ticket asíncrono que requiere consultar getStatus(ticket).
    - ConsultarTicketView maneja ese flujo.
    """

    def post(self, request, pk):
        """Procesa el envío de un comprobante individual y actualiza su estado."""
        try:
            comprobante = Comprobante.objects.get(pk=pk)
        except Comprobante.DoesNotExist:
            return JsonResponse({'error': 'Comprobante no encontrado'}, status=404)

        if comprobante.estado not in ['EMITIDO', 'RECHAZADO', 'BORRADOR']:
            return JsonResponse({
                'error': f'No se puede enviar comprobante en estado {comprobante.estado}'
            }, status=400)

        try:
            # 1. Generar y firmar el XML UBL 2.1
            xml_content = generar_xml_ubl(comprobante)
            from .xml_generator import firmar_xml
            xml_firmado = firmar_xml(xml_content)

            # 2. Empaquetar en ZIP con el nombre SUNAT requerido
            nombre_zip = comprobante.nombre_zip.replace('.zip', '')
            zip_content = crear_zip(xml_firmado, nombre_zip)
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')

            # 3. Obtener el cliente OSE (Mock o Real segun settings)
            ose_client = get_ose_client()
            file_name = (
                f"{comprobante.empresa.ruc}-{comprobante.tipo}"
                f"-{comprobante.serie.serie}-{comprobante.numero:08d}.zip"
            )

            logger.info(f"Enviando comprobante {comprobante} al OSE...")
            respuesta = ose_client.send_bill(zip_base64, file_name)
            logger.info(f"Respuesta OSE: status={respuesta.get('status')}")

            # 4. Guardar XML firmado independientemente del resultado
            comprobante.xml_firmado = (
                xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
            )

            if respuesta.get('status') == 0:
                # EXITO: sendBill retorna CDR inmediato en 'applicationResponse'.
                # Para comprobantes individuales NO hay ticket asincrono.
                # El comprobante ya fue ACEPTADO por SUNAT en esta misma llamada.
                cdr_b64 = respuesta.get('applicationResponse', '')

                LogEnvioSUNAT.objects.create(
                    comprobante=comprobante,
                    estado_respuesta='ACEPTADO',
                    codigo_respuesta='0',
                    descripcion='CDR recibido - Comprobante aceptado por SUNAT/OSE',
                    uuid=respuesta.get('ticket', ''),
                    cdr_xml=cdr_b64
                )

                # sunat_ticket queda en None para sendBill (solo sendPack usa ticket)
                ticket_valor = respuesta.get('ticket') or None
                comprobante.sunat_ticket = ticket_valor
                comprobante.estado = 'ACEPTADO'
                comprobante.save(update_fields=['xml_firmado', 'sunat_ticket', 'estado'])

                return JsonResponse({
                    'success': True,
                    'message': 'Comprobante aceptado por SUNAT',
                    'ticket': ticket_valor,
                    'estado': 'ACEPTADO',
                    'cdr': bool(cdr_b64),
                })
            else:
                # RECHAZO: OSE/SUNAT devolvio un error de negocio o estructura
                LogEnvioSUNAT.objects.create(
                    comprobante=comprobante,
                    estado_respuesta='RECHAZADO',
                    codigo_respuesta=str(respuesta.get('status', '-1')),
                    descripcion=respuesta.get('faultstring') or 'Rechazado por OSE/SUNAT',
                    uuid=''
                )

                comprobante.estado = 'RECHAZADO'
                comprobante.save(update_fields=['xml_firmado', 'estado'])

                return JsonResponse({
                    'success': False,
                    'error': respuesta.get('faultstring', 'Error en el envio'),
                    'codigo': respuesta.get('faultcode', 'UNKNOWN'),
                    'estado': 'RECHAZADO'
                }, status=400)

        except Exception as e:
            logger.error(f"Error enviando comprobante {pk}: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class ConsultarTicketView(View):
    """
    Vista para consultar el estado de un ticket en el OSE.
    
    Flujo real:
    1. Obtener ticket del comprobante
    2. Consultar get_status(ticket) al OSE
    3. Si status=0 (aceptado), obtener CDR con getStatusCdr
    4. Actualizar estado del comprobante
    5. Guardar CDR en log
    """
    
    def post(self, request, pk):
        try:
            comprobante = Comprobante.objects.get(pk=pk)
        except Comprobante.DoesNotExist:
            return JsonResponse({'error': 'Comprobante no encontrado'}, status=404)

        if not comprobante.sunat_ticket:
            return JsonResponse({'error': 'No existe ticket para este comprobante'}, status=400)

        try:
            ose_client = get_ose_client()
            
            logger.info(f"Consultando ticket {comprobante.sunat_ticket} para comprobante {comprobante}")
            
            respuesta_status = ose_client.get_status(comprobante.sunat_ticket)
            
            logger.info(f"Estado ticket: {respuesta_status}")
            
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
                
                LogEnvioSUNAT.objects.create(
                    comprobante=comprobante,
                    estado_respuesta='ACEPTADO',
                    codigo_respuesta='0',
                    descripcion='CDR recibido - Comprobante aceptado por SUNAT',
                    uuid=comprobante.sunat_ticket,
                    cdr_xml=cdr_base64
                )
                
                comprobante.estado = 'ACEPTADO'
                comprobante.save(update_fields=['estado'])
                
                return JsonResponse({
                    'success': True,
                    'estado': 'ACEPTADO',
                    'descripcion': 'Comprobante aceptado por SUNAT',
                    'ticket': comprobante.sunat_ticket
                })
            elif respuesta_status.get('status') == 99:
                comprobante.estado = 'RECHAZADO'
                comprobante.save(update_fields=['estado'])
                
                return JsonResponse({
                    'success': False,
                    'estado': 'RECHAZADO',
                    'descripcion': respuesta_status.get('faultstring', 'Rechazado por SUNAT'),
                    'codigo': respuesta_status.get('faultcode', 'UNKNOWN')
                })
            else:
                return JsonResponse({
                    'success': True,
                    'estado': 'PROCESANDO',
                    'descripcion': 'El comprobante aún está siendo procesado',
                    'ticket': comprobante.sunat_ticket
                })

        except Exception as e:
            logger.error(f"Error consultando ticket para comprobante {pk}: {str(e)}", exc_info=True)
            return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)


@login_required
def envio_masivo(request):
    empresa = request.GET.get('empresa')
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', 'EMITIDO')

    comprobantes = Comprobante.objects.select_related('cliente', 'empresa', 'serie')
    
    if empresa:
        comprobantes = comprobantes.filter(empresa_id=empresa)
    if tipo:
        comprobantes = comprobantes.filter(tipo=tipo)
    if estado:
        comprobantes = comprobantes.filter(estado=estado)

    comprobantes = comprobantes.filter(estado__in=['EMITIDO', 'BORRADOR'])[:100]

    from apps.empresas.models import Empresa
    empresas = Empresa.objects.all()

    lotes = LoteEnvio.objects.order_by('-fecha_creacion')[:10]

    return render(request, 'sunat_ose/envio_masivo.html', {
        'comprobantes': comprobantes,
        'empresas': empresas,
        'lotes': lotes,
        'filtros': {'empresa': empresa, 'tipo': tipo, 'estado': estado}
    })


@login_required
def enviar_lote(request):
    if request.method != 'POST':
        return redirect('sunat_ose:envio_masivo')

    comprobante_ids = request.POST.getlist('comprobantes')
    if not comprobante_ids:
        messages.error(request, 'No se seleccionaron comprobantes')
        return redirect('sunat_ose:envio_masivo')

    try:
        comprobantes = Comprobante.objects.filter(
            id__in=comprobante_ids,
            estado__in=['EMITIDO', 'BORRADOR']
        ).select_related('empresa')

        if not comprobantes.exists():
            messages.error(request, 'No se encontraron comprobantes válidos')
            return redirect('sunat_ose:envio_masivo')

        empresa = comprobantes.first().empresa
        fecha_emision = date.today()

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('dummy/', b'')
            for comprobante in comprobantes:
                xml_content = generar_xml_ubl(comprobante)
                from .xml_generator import firmar_xml
                xml_firmado = firmar_xml(xml_content)
                nombre_xml = comprobante.nombre_xml
                zf.writestr(nombre_xml, xml_firmado if isinstance(xml_firmado, bytes) else xml_firmado.encode('utf-8'))

        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        zip_base64 = base64.b64encode(zip_content).decode('utf-8')

        file_name = f"{empresa.ruc}-LT-{fecha_emision.strftime('%Y%m%d')}-1.zip"

        ose_client = get_ose_client()
        respuesta = ose_client.send_pack(zip_base64, file_name)

        lote = LoteEnvio.objects.create(
            empresa=empresa,
            fecha_emision_documentos=fecha_emision,
            total_documentos=comprobantes.count(),
            estado='PENDIENTE',
            ticket_ose=respuesta.get('ticket'),
            observacion=f"Enviados: {comprobantes.count()}"
        )

        if respuesta.get('status') == 0:
            lote.estado = 'PROCESANDO'
            lote.save()
            messages.success(request, f'Lote enviado exitosamente. Ticket: {lote.ticket_ose}')
        else:
            lote.estado = 'ERROR'
            lote.observacion = respuesta.get('faultstring', 'Error en envío')
            lote.save()
            messages.error(request, f'Error enviando lote: {lote.observacion}')

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        logger.error(f"Error en envío masivo: {str(e)}", exc_info=True)

    return redirect('sunat_ose:envio_masivo')