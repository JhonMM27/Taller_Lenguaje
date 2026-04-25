from django.contrib import admin
from .models import NotaCredito


@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = ['numero_completo', 'comprobante_referencia', 'fecha', 'monto_afectado', 'estado']
    list_filter = ['tipo_nota', 'estado']
    search_fields = ['serie', 'numero', 'comprobante_referencia__numero']

    def numero_completo(self, obj):
        return f"{obj.serie}-{obj.numero:08d}"
    numero_completo.short_description = 'Número'