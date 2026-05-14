from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.empresas.models import Empresa
from apps.empresas.forms import EmpresaForm


@login_required
def lista_empresas(request):
    empresas = Empresa.objects.all()
    return render(request, 'empresas/lista.html', {
        'empresas': empresas.order_by('-created_at')[:100]
    })


@login_required
def crear_empresa(request):
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            empresa = form.save()
            messages.success(request, 'Empresa creada exitosamente')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Empresa creada correctamente', 'redirect_url': '/empresas/'})
            return redirect('empresas:lista')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = dict(form.errors)
            return JsonResponse({'success': False, 'error': 'Por favor corrija los errores', 'form_errors': errors}, status=400)
        return render(request, 'empresas/crear.html', {'form': form})
    form = EmpresaForm()
    return render(request, 'empresas/crear.html', {'form': form})


@login_required
def editar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        form = EmpresaForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa actualizada exitosamente')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Empresa actualizada correctamente', 'redirect_url': '/empresas/'})
            return redirect('empresas:lista')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            errors = dict(form.errors)
            return JsonResponse({'success': False, 'error': 'Por favor corrija los errores', 'form_errors': errors}, status=400)
        return render(request, 'empresas/editar.html', {'form': form, 'empresa': empresa})
    form = EmpresaForm(instance=empresa)
    return render(request, 'empresas/editar.html', {'form': form, 'empresa': empresa})


@login_required
def eliminar_empresa(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk)
    if request.method == 'POST':
        empresa.delete()
        messages.success(request, 'Empresa eliminada exitosamente')
        return redirect('empresas:lista')
    return render(request, 'empresas/eliminar.html', {'empresa': empresa})