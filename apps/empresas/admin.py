from django.contrib import admin
from .models import Empresa


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['ruc', 'razon_social', 'regimen_tributario', 'telefono', 'email']
    search_fields = ['ruc', 'razon_social']
    list_filter = ['regimen_tributario']