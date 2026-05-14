from django.contrib import admin
from .models import Empresa, Certificado


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['ruc', 'razon_social', 'regimen_tributario', 'telefono', 'email']
    search_fields = ['ruc', 'razon_social']
    list_filter = ['regimen_tributario']


@admin.register(Certificado)
class CertificadoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'empresa', 'numero_serie', 'fecha_desde', 'fecha_hasta', 'is_active']
    search_fields = ['nombre', 'empresa__ruc', 'empresa__razon_social', 'numero_serie']
    list_filter = ['is_active', 'empresa']
    readonly_fields = ['empresa', 'nombre', 'numero_serie', 'fecha_desde', 'fecha_hasta', 'huella_digital', 'created_at', 'updated_at', 'contrasena']
    fields = ['empresa', 'nombre', 'numero_serie', 'fecha_desde', 'fecha_hasta', 'huella_digital', 'is_active', 'contrasena']