from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.notas_credito.models import NotaCredito
from apps.notas_credito.serializers import NotaCreditoSerializer
from apps.comprobantes.models import Comprobante


@login_required
def lista_notas_credito(request):
    notas = NotaCredito.objects.select_related('comprobante_referencia').all()
    from datetime import datetime
    return render(request, 'notas_credito/lista.html', {
        'notas': notas.order_by('-fecha', '-created_at')[:50],
        'comprobantes': Comprobante.objects.filter(estado='ACEPTADO').select_related('cliente')[:50],
        'motivos': NotaCredito.MOTIVO_CHOICES,
        'today': datetime.now()
    })


@login_required
def crear_nota_credito(request):
    if request.method == 'POST':
        comprobante_id = request.POST.get('comprobante_referencia')
        tipo_nota = request.POST.get('tipo_nota')
        monto_afectado = request.POST.get('monto_afectado')
        descripcion = request.POST.get('descripcion', '')
        
        serie = request.POST.get('serie', 'FF01')
        numero = request.POST.get('numero', '1')
        
        comprobante = get_object_or_404(Comprobante, pk=comprobante_id)
        
        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=serie,
            numero=int(numero),
            fecha=request.POST.get('fecha'),
            tipo_nota=tipo_nota,
            monto_afectado=monto_afectado,
            descripcion=descripcion,
            estado='BORRADOR'
        )
        messages.success(request, 'Nota de Crédito creada exitosamente')
        return redirect('notas_credito:lista')
    
    comprobantes = Comprobante.objects.filter(estado='ACEPTADO').select_related('cliente')[:50]
    return render(request, 'notas_credito/crear.html', {
        'comprobantes': comprobantes,
        'motivos': NotaCredito.MOTIVO_CHOICES
    })


@login_required
def detalle_nota_credito(request, pk):
    nota = get_object_or_404(NotaCredito.objects.select_related('comprobante_referencia', 'comprobante_referencia__cliente'), pk=pk)
    return render(request, 'notas_credito/detalle.html', {'nota': nota})


@login_required
def eliminar_nota_credito(request, pk):
    nota = get_object_or_404(NotaCredito, pk=pk)
    if request.method == 'POST':
        nota.delete()
        messages.success(request, 'Nota de Crédito eliminada exitosamente')
        return redirect('notas_credito:lista')
    return render(request, 'notas_credito/eliminar.html', {'nota': nota})