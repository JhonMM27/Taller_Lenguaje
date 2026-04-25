from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['num_doc', 'razon_social', 'tipo_doc', 'email', 'telefono']
    search_fields = ['num_doc', 'razon_social', 'email']
    list_filter = ['tipo_doc']