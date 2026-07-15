from django.contrib import admin
from .models import Producto, CategoriaProducto


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'codigo_sunat', 'activo']
    search_fields = ['nombre', 'codigo_sunat']
    list_filter = ['activo']


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'precio_unitario', 'categoria', 'tipo_operacion', 'afecto_igv']
    search_fields = ['codigo', 'descripcion']
    list_filter = ['afecto_igv', 'tipo_operacion', 'categoria']