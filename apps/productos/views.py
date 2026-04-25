from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.productos.models import Producto, CategoriaProducto
from apps.productos.serializers import ProductoSerializer, CategoriaProductoSerializer


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
    categorias = CategoriaProducto.objects.filter(activa=True).order_by('nombre')
    if request.method == 'POST':
        serializer = ProductoSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Producto creado exitosamente')
            return redirect('productos:lista')
        return render(request, 'productos/crear.html', {'errors': serializer.errors, 'categorias': categorias})
    return render(request, 'productos/crear.html', {'categorias': categorias})


@login_required
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    categorias = CategoriaProducto.objects.filter(activa=True).order_by('nombre')
    if request.method == 'POST':
        serializer = ProductoSerializer(instance=producto, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('productos:lista')
        return render(request, 'productos/editar.html', {'errors': serializer.errors, 'producto': producto, 'categorias': categorias})
    return render(request, 'productos/editar.html', {'producto': producto, 'categorias': categorias})


@login_required
def eliminar_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == 'POST':
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente')
        return redirect('productos:lista')
    return render(request, 'productos/eliminar.html', {'producto': producto})


@login_required
def lista_categorias(request):
    query = request.GET.get('q', '')
    if query:
        categorias = CategoriaProducto.objects.filter(nombre__icontains=query)
    else:
        categorias = CategoriaProducto.objects.all()
    return render(request, 'productos/categorias/lista.html', {
        'categorias': categorias.order_by('nombre'),
        'query': query
    })


@login_required
def crear_categoria(request):
    if request.method == 'POST':
        serializer = CategoriaProductoSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Categoría creada exitosamente')
            return redirect('productos:categorias_lista')
        return render(request, 'productos/categorias/crear.html', {'errors': serializer.errors})
    return render(request, 'productos/categorias/crear.html')


@login_required
def editar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    if request.method == 'POST':
        serializer = CategoriaProductoSerializer(instance=categoria, data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, 'Categoría actualizada exitosamente')
            return redirect('productos:categorias_lista')
        return render(request, 'productos/categorias/editar.html', {'errors': serializer.errors, 'categoria': categoria})
    return render(request, 'productos/categorias/editar.html', {'categoria': categoria})


@login_required
def eliminar_categoria(request, pk):
    categoria = get_object_or_404(CategoriaProducto, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoría eliminada exitosamente')
        return redirect('productos:categorias_lista')
    return render(request, 'productos/categorias/eliminar.html', {'categoria': categoria})