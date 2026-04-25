from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.productos.models import Producto
from apps.productos.serializers import ProductoSerializer


@login_required
def lista_productos(request):
    query = request.GET.get('q', '')
    if query:
        productos = Producto.objects.filter(
            descripcion__icontains=query
        ) | Producto.objects.filter(codigo__icontains=query)
    else:
        productos = Producto.objects.all()
    return render(request, 'productos/lista.html', {
        'productos': productos.order_by('-created_at')[:100],
        'query': query
    })


@login_required
def crear_producto(request):
    if request.method == 'POST':
        serializer = ProductoSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Producto creado exitosamente')
            return redirect('productos:lista')
        return render(request, 'productos/crear.html', {'errors': serializer.errors})
    return render(request, 'productos/crear.html')


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        serializer = ProductoSerializer(instance=producto, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('productos:lista')
        return render(request, 'productos/editar.html', {'errors': serializer.errors, 'producto': producto})
    return render(request, 'productos/editar.html', {'producto': producto})


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente')
        return redirect('productos:lista')
    return render(request, 'productos/eliminar.html', {'producto': producto})