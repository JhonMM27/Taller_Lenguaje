from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.empresas.models import Empresa
from apps.empresas.serializers import EmpresaSerializer


@login_required
def lista_empresas(request):
    empresas = Empresa.objects.all()
    return render(request, 'empresas/lista.html', {
        'empresas': empresas.order_by('-created_at')[:100]
    })


@login_required
def crear_empresa(request):
    if request.method == 'POST':
        serializer = EmpresaSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Empresa creada exitosamente')
            return redirect('empresas:lista')
        return render(request, 'empresas/crear.html', {'errors': serializer.errors})
    return render(request, 'empresas/crear.html')


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        serializer = EmpresaSerializer(instance=empresa, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Empresa actualizada exitosamente')
            return redirect('empresas:lista')
        return render(request, 'empresas/editar.html', {'errors': serializer.errors, 'empresa': empresa})
    return render(request, 'empresas/editar.html', {'empresa': empresa})


@login_required
def eliminar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        messages.success(request, 'Empresa eliminada exitosamente')
        return redirect('empresas:lista')
    return render(request, 'empresas/eliminar.html', {'empresa': empresa})