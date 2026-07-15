from django.contrib import admin
from .models import PerfilUsuario

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'rol', 'empresa', 'activo', 'creado_en']
    list_filter = ['rol', 'activo']
    search_fields = ['usuario__username', 'empresa__razon_social']
