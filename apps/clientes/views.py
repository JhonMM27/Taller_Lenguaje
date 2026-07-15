from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.clientes.models import Cliente
from apps.clientes.serializers import ClienteSerializer


@login_required
def lista_clientes(request):
    query = request.GET.get('q', '')
    if query:
        clientes = Cliente.objects.filter(
            razon_social__icontains=query
        ) | Cliente.objects.filter(num_doc__icontains=query)
    else:
        clientes = Cliente.objects.all()
    return render(request, 'clientes/lista.html', {
        'clientes': clientes.order_by('-creado_en')[:100],
        'query': query
    })


@login_required
def crear_cliente(request):
    if request.method == 'POST':
        serializer = ClienteSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Cliente creado exitosamente')
            return redirect('clientes:lista')
        return render(request, 'clientes/crear.html', {'errors': serializer.errors})
    return render(request, 'clientes/crear.html')


@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        serializer = ClienteSerializer(instance=cliente, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Cliente actualizado exitosamente')
            return redirect('clientes:lista')
        return render(request, 'clientes/editar.html', {'errors': serializer.errors, 'cliente': cliente})
    return render(request, 'clientes/editar.html', {'cliente': cliente})


@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.eliminar(usuario=request.user)
        messages.success(request, 'Cliente eliminado exitosamente')
        return redirect('clientes:lista')
    return render(request, 'clientes/eliminar.html', {'cliente': cliente})