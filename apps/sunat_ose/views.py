from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from .xml_generator import generar_xml_ubl, crear_zip
from .ose_client import get_ose_client
import logging
import base64

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EnviarComprobanteView(View):
    """
    Vista para enviar un comprobante al OSE (Mock o Real).
    
    Flujo real:
    1. Generar XML UBL 2.1
    2. Firmar XML (en mock returns sin firma real)
    3. Crear ZIP con el XML
    4. Enviar via SOAP sendBill al OSE
    5. Obtener ticket de respuesta
    6. Guardar ticket en comprobante
    7. Guardar Log del envío
    """
    
    def post(self, request, pk):
        try:
            comprobante = Comprobante.objects.get(pk=pk)
        except Comprobante.DoesNotExist:
            return JsonResponse({'error': 'Comprobante no encontrado'}, status=404)

        if comprobante.estado not in ['EMITIDO', 'RECHAZADO', 'BORRADOR']:
            return JsonResponse({
                'error': f'No se puede enviar comprobante en estado {comprobante.estado}'
            }, status=400)

        try:
            xml_content = generar_xml_ubl(comprobante)
            
            from .xml_generator import firmar_xml
            xml_firmado = firmar_xml(xml_content)
            
            nombre_zip = comprobante.nombre_zip.replace('.zip', '')
            zip_content = crear_zip(xml_firmado, nombre_zip)
            
            zip_base64 = base64.b64encode(zip_content).decode('utf-8')
            
            ose_client = get_ose_client()
            
            file_name = f"{comprobante.empresa.ruc}-{comprobante.tipo}-{comprobante.serie.serie}-{comprobante.numero:08d}.zip"
            
            logger.info(f"Enviando comprobante {comprobante} al OSE...")
            
            respuesta = ose_client.send_bill(zip_base64, file_name)
            
            logger.info(f"Respuesta OSE: {respuesta}")
            
            estado_log = 'RECHAZADO' if respuesta.get('status') != 0 else 'ENVIADO'
            
            LogEnvioSUNAT.objects.create(
                comprobante=comprobante,
                estado_respuesta=estado_log,
                codigo_respuesta=str(respuesta.get('status', '-1')),
                descripcion=respuesta.get('faultstring') or 'Envío procesado',
                uuid=respuesta.get('ticket', '')
            )
            
            if respuesta.get('status') == 0:
                comprobante.sunat_ticket = respuesta.get('ticket')
                comprobante.estado = 'ENVIADO'
                comprobante.xml_firmado = xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
                comprobante.save(update_fields=['xml_firmado', 'sunat_ticket', 'estado'])
                
                return JsonResponse({
                    'success': True,
                    'message': 'Comprobante enviado exitosamente',
                    'ticket': respuesta.get('ticket'),
                    'estado': 'ENVIADO'
                })
            else:
                comprobante.estado = 'RECHAZADO'
                comprobante.save(update_fields=['estado'])
                
                return JsonResponse({
                    'success': False,
                    'error': respuesta.get('faultstring', 'Error en el envío'),
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