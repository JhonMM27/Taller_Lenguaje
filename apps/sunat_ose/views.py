"""
Views del módulo SUNAT/OSE.

Views delgadas: delegan al SunatEnvioService.
"""

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.comprobantes.models import Comprobante
from apps.sunat_ose.models import LoteEnvio
from apps.sunat_ose.services import SunatEnvioService
from apps.core.exceptions import (
    AppError, ComprobanteNoEncontrado, EstadoInvalido,
    FirmaDigitalInvalida, EnvioSunatFallido, TicketNoEncontrado,
)

import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class EnviarComprobanteView(View):
    """View delgada: delega al SunatEnvioService.enviar()."""

    def post(self, request, pk):
        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        try:
            resultado = SunatEnvioService.enviar(pk)
            resultado['advertencia'] = (
                'MODO MOCK ACTIVADO - NO se envio a SUNAT real' if es_mock else None
            )
            return JsonResponse(resultado)
        except ComprobanteNoEncontrado as e:
            return JsonResponse({'success': False, 'error': str(e), 'es_mock': es_mock}, status=404)
        except EstadoInvalido as e:
            return JsonResponse({'success': False, 'error': str(e), 'es_mock': es_mock}, status=400)
        except FirmaDigitalInvalida as e:
            return JsonResponse({
                'success': False, 'error': str(e),
                'codigo': 'FIRMA_INVALIDA', 'estado': 'ERROR_FIRMA', 'es_mock': es_mock,
            }, status=500)
        except EnvioSunatFallido as e:
            return JsonResponse({
                'success': False, 'error': str(e),
                'codigo': 'RECHAZADO', 'estado': 'RECHAZADO', 'es_mock': es_mock,
            }, status=400)
        except AppError as e:
            logger.error(f"Error enviando comprobante {pk}: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False, 'error': str(e),
                'codigo': 'ERROR_INTERNO', 'estado': 'ERROR', 'es_mock': es_mock,
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class EnviarNotaCreditoView(View):
    """View delgada: delega al SunatEnvioService.enviar_nota_credito()."""

    def post(self, request, pk):
        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        try:
            resultado = SunatEnvioService.enviar_nota_credito(pk)
            resultado['advertencia'] = (
                'MODO MOCK ACTIVADO - NO se envio a SUNAT real' if es_mock else None
            )
            return JsonResponse(resultado)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error enviando nota de credito {pk}: {error_msg}", exc_info=True)
            return JsonResponse({
                'success': False,
                'error': error_msg,
                'codigo': 'ERROR',
                'es_mock': es_mock,
            }, status=400)


@method_decorator(csrf_exempt, name='dispatch')
class ConsultarTicketView(View):
    """View delgada: delega al SunatEnvioService.consultar_ticket()."""

    def post(self, request, pk):
        try:
            resultado = SunatEnvioService.consultar_ticket(pk)
            return JsonResponse(resultado)
        except ComprobanteNoEncontrado as e:
            return JsonResponse({'error': str(e)}, status=404)
        except TicketNoEncontrado as e:
            return JsonResponse({'error': str(e)}, status=400)
        except EnvioSunatFallido as e:
            return JsonResponse({
                'success': False, 'estado': 'RECHAZADO',
                'descripcion': str(e),
            })
        except AppError as e:
            logger.error(f"Error consultando ticket para {pk}: {str(e)}", exc_info=True)
            return JsonResponse({'error': str(e)}, status=500)


@login_required
def envio_masivo(request):
    empresa = request.GET.get('empresa')
    tipo = request.GET.get('tipo', '')
    estado = request.GET.get('estado', '')

    comprobantes = Comprobante.objects.select_related('cliente', 'empresa', 'serie')
    
    if empresa:
        comprobantes = comprobantes.filter(empresa_id=empresa)
    if tipo:
        comprobantes = comprobantes.filter(tipo=tipo)
    if estado:
        comprobantes = comprobantes.filter(estado=estado)
    else:
        # Por defecto, mostrar comprobantes listos para enviar (EMITIDO, BORRADOR y RECHAZADO)
        comprobantes = comprobantes.filter(estado__in=['EMITIDO', 'BORRADOR', 'RECHAZADO'])

    comprobantes = comprobantes.order_by('-fecha', '-creado_en')

    from django.core.paginator import Paginator
    paginator = Paginator(comprobantes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Consultar los últimos comprobantes procesados/enviados
    comprobantes_enviados = Comprobante.objects.filter(
        estado__in=['ACEPTADO', 'ENVIADO']
    ).select_related('cliente', 'empresa', 'serie').order_by('-fecha', '-numero')[:50]

    from apps.empresas.models import Empresa
    empresas = Empresa.objects.all()

    lotes = LoteEnvio.objects.order_by('-creado_en')[:10]

    return render(request, 'sunat_ose/envio_masivo.html', {
        'comprobantes': page_obj,
        'enviados': comprobantes_enviados,
        'empresas': empresas,
        'lotes': lotes,
        'filtros': {'empresa': empresa, 'tipo': tipo, 'estado': estado}
    })


@login_required
def enviar_lote(request):
    """View delgada: delega al SunatEnvioService.enviar_lote()."""
    if request.method != 'POST':
        return redirect('sunat_ose:envio_masivo')

    comprobante_ids = request.POST.getlist('comprobantes')
    if not comprobante_ids:
        messages.error(request, 'No se seleccionaron comprobantes')
        return redirect('sunat_ose:envio_masivo')

    try:
        lote = SunatEnvioService.enviar_lote(comprobante_ids, usuario=request.user)
        messages.success(request, f'Lote enviado exitosamente. Ticket: {lote.ticket_ose}')
    except EstadoInvalido as e:
        messages.error(request, str(e))
    except EnvioSunatFallido as e:
        messages.error(request, f'Error enviando lote: {str(e)}')
    except AppError as e:
        messages.error(request, f'Error: {str(e)}')
        logger.error(f"Error en envío masivo: {str(e)}", exc_info=True)

    return redirect('sunat_ose:envio_masivo')


@method_decorator(csrf_exempt, name='dispatch')
class ConsultarLoteView(View):
    """View delgada: delega al SunatEnvioService.consultar_lote()."""

    def post(self, request, pk):
        try:
            resultado = SunatEnvioService.consultar_lote(pk)
            return JsonResponse(resultado)
        except Exception as e:
            logger.error(f"Error consultando ticket de lote {pk}: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def descargar_cdr_lote(request, pk):
    """
    Consolida todos los CDRs (ZIPs) de los comprobantes enviados en un lote
    en un único archivo ZIP comprimido.
    """
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    import zipfile
    from io import BytesIO
    import base64

    lote = get_object_or_404(LoteEnvio, pk=pk)

    # Los IDs de comprobantes exitosos se guardan como CSV en ticket_ose
    if not lote.ticket_ose or lote.ticket_ose == 'NONE':
        return HttpResponse("Este lote no tiene comprobantes con CDR disponible.", status=400)

    try:
        comprobante_ids = [int(x.strip()) for x in lote.ticket_ose.split(',') if x.strip().isdigit()]
    except (ValueError, AttributeError):
        return HttpResponse("No se pudieron obtener los comprobantes de este lote.", status=400)

    if not comprobante_ids:
        return HttpResponse("No se encontraron comprobantes asociados a este lote.", status=404)

    comprobantes = Comprobante.objects.filter(id__in=comprobante_ids)

    # Crear archivo ZIP consolidado en memoria
    zip_in_memory = BytesIO()

    with zipfile.ZipFile(zip_in_memory, 'w', zipfile.ZIP_STORED) as zf:
        agregados = 0
        for comp in comprobantes:
            # Buscar el CDR más reciente en los logs
            log_cdr = comp.logs.filter(cdr_xml__isnull=False).exclude(cdr_xml='').first()
            if log_cdr and log_cdr.cdr_xml:
                try:
                    cdr_bytes = base64.b64decode(log_cdr.cdr_xml)
                    nombre_cdr_zip = f"R-{comp.nombre_zip}"
                    zf.writestr(nombre_cdr_zip, cdr_bytes)
                    agregados += 1
                except Exception as e:
                    logger.error(f"Error decodificando CDR para {comp.id}: {str(e)}")

        if agregados == 0:
            return HttpResponse("Ninguno de los comprobantes de este lote tiene un CDR disponible.", status=404)

    zip_in_memory.seek(0)
    response = HttpResponse(zip_in_memory.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Lote-{lote.id}-CDRs.zip"'
    return response