from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.notas_credito.models import NotaCredito
from apps.notas_credito.serializers import NotaCreditoSerializer
from apps.comprobantes.models import Comprobante


@login_required
def lista_notas_credito(request):
    notas = NotaCredito.objects.select_related('comprobante_referencia').all()
    return render(request, 'notas_credito/lista.html', {
        'notas': notas.order_by('-fecha', '-created_at')[:50],
    })


@login_required
def crear_nota_credito(request):
    if request.method == 'POST':
        comprobante_id = request.POST.get('comprobante_referencia')
        tipo_nc = request.POST.get('tipo_nc')
        tipo_nota = request.POST.get('tipo_nota')
        descripcion = request.POST.get('descripcion', '')

        comprobante = get_object_or_404(Comprobante, pk=comprobante_id)

        serie = 'FC01'
        if comprobante.serie:
            if comprobante.serie.tipo == '01':
                serie = 'FC' + comprobante.serie.serie[2:] if len(comprobante.serie.serie) >= 2 else 'FC01'
            elif comprobante.serie.tipo == '03':
                serie = 'FB' + comprobante.serie.serie[2:] if len(comprobante.serie.serie) >= 2 else 'FB01'

        notas_existentes = NotaCredito.objects.filter(serie=serie).count()
        numero = notas_existentes + 1

        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=serie,
            numero=numero,
            tipo_nc=tipo_nc,
            tipo_nota=tipo_nota,
            descripcion=descripcion,
            estado='BORRADOR'
        )
        messages.success(request, 'Nota de Crédito creada exitosamente')
        return redirect('notas_credito:lista')

    return render(request, 'notas_credito/crear.html', {
        'motivos_nc': NotaCredito.MOTIVO_NC,
        'motivos_ncd': NotaCredito.MOTIVO_NCD,
    })


@login_required
def detalle_nota_credito(request, pk):
    nota = get_object_or_404(
        NotaCredito.objects.select_related('comprobante_referencia', 'comprobante_referencia__cliente'),
        pk=pk
    )
    detalles = nota.detalles.select_related('producto').all()
    return render(request, 'notas_credito/detalle.html', {
        'nota': nota,
        'detalles': detalles,
    })


@login_required
def eliminar_nota_credito(request, pk):
    nota = get_object_or_404(NotaCredito, pk=pk)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota de Crédito eliminada exitosamente')
        return redirect('notas_credito:lista')
    return render(request, 'notas_credito/eliminar.html', {'nota': nota})
