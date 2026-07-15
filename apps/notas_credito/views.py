"""
Views web del módulo de Notas de Crédito.

Views delgadas: delegan al NotaCreditoService.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.notas_credito.models import NotaCredito
from apps.notas_credito.services import NotaCreditoService
from apps.comprobantes.models import Comprobante
from apps.core.exceptions import (
    AppError, MontoExcedidoError, ComprobanteNoAceptado,
    ComprobanteNoEncontrado, RecursoNoEncontrado,
)


@login_required
def lista_notas_credito(request):
    notas = NotaCredito.objects.select_related('comprobante_referencia').all()
    return render(request, 'notas_credito/lista.html', {
        'notas': notas.order_by('-fecha', '-creado_en')[:50],
    })


@login_required
def crear_nota_credito(request):
    """View delgada: delega al NotaCreditoService.emitir()."""
    if request.method == 'POST':
        try:
            nota = NotaCreditoService.emitir(
                data={
                    'comprobante_id': request.POST.get('comprobante_referencia'),
                    'tipo_nc': request.POST.get('tipo_nc'),
                    'tipo_nota': request.POST.get('tipo_nota'),
                    'descripcion': request.POST.get('descripcion', ''),
                    'monto_afectado': request.POST.get('monto_afectado', 0),
                },
                usuario=request.user,
            )
            messages.success(request, f'Nota de Crédito {nota} creada exitosamente')
            return redirect('notas_credito:lista')
        except MontoExcedidoError as e:
            messages.error(request, str(e))
        except ComprobanteNoAceptado as e:
            messages.error(request, str(e))
        except ComprobanteNoEncontrado as e:
            messages.error(request, str(e))
        except AppError as e:
            messages.error(request, str(e))

    return render(request, 'notas_credito/crear.html', {
        'motivos_nc': NotaCredito.MOTIVO_NC,
        'motivos_ncd': NotaCredito.MOTIVO_NCD,
    })


@login_required
def detalle_nota_credito(request, pk):
    nota = get_object_or_404(
        NotaCredito.objects.select_related(
            'comprobante_referencia', 'comprobante_referencia__cliente'
        ),
        pk=pk
    )
    detalles = nota.detalles.select_related('producto').all()
    return render(request, 'notas_credito/detalle.html', {
        'nota': nota,
        'detalles': detalles,
    })


@login_required
def eliminar_nota_credito(request, pk):
    """Soft delete — nunca borrar físicamente."""
    if request.method == 'POST':
        try:
            NotaCreditoService.eliminar(pk, usuario=request.user)
            messages.success(request, 'Nota de Crédito eliminada exitosamente')
        except RecursoNoEncontrado as e:
            messages.error(request, str(e))
        return redirect('notas_credito:lista')

    nota = get_object_or_404(NotaCredito, pk=pk)
    return render(request, 'notas_credito/eliminar.html', {'nota': nota})


from django.http import HttpResponse

@login_required
def descargar_xml(request, pk):
    nota = get_object_or_404(NotaCredito, pk=pk)
    if not nota.xml_firmado:
        return HttpResponse("XML no disponible", status=404)

    import xml.dom.minidom
    try:
        dom = xml.dom.minidom.parseString(nota.xml_firmado)
        pretty_xml = dom.toprettyxml(indent="  ")
        pretty_xml = "\n".join([line for line in pretty_xml.splitlines() if line.strip()])
    except Exception:
        pretty_xml = nota.xml_firmado

    response = HttpResponse(pretty_xml.encode('utf-8'), content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="{nota.nombre_xml}"'
    return response


@login_required
def descargar_cdr(request, pk):
    nota = get_object_or_404(NotaCredito, pk=pk)
    if not nota.cdr_xml:
        return HttpResponse("El CDR no está disponible para esta nota de crédito.", status=404)

    try:
        import base64
        cdr_bytes = base64.b64decode(nota.cdr_xml)
        nombre_cdr_zip = f"R-{nota.nombre_zip}"
        
        response = HttpResponse(cdr_bytes, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{nombre_cdr_zip}"'
        return response
    except Exception as e:
        return HttpResponse(f"Error al procesar el archivo del CDR: {str(e)}", status=500)
