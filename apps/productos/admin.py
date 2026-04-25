from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descripcion', 'precio_unitario', 'afecto_igv']
    search_fields = ['codigo', 'descripcion']
    list_filter = ['afecto_igv']