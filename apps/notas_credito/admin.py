from django.contrib import admin
from .models import NotaCredito, DetalleNotaCredito


class DetalleNotaCreditoInline(admin.TabularInline):
    model = DetalleNotaCredito
    extra = 0
    readonly_fields = ['igv_linea', 'subtotal']


@admin.register(NotaCredito)
class NotaCreditoAdmin(admin.ModelAdmin):
    list_display = ['numero_completo', 'tipo_nc', 'comprobante_referencia', 'fecha', 'importe', 'estado']
    list_filter = ['tipo_nc', 'tipo_nota', 'estado']
    search_fields = ['serie', 'numero', 'comprobante_referencia__numero']
    inlines = [DetalleNotaCreditoInline]

    def numero_completo(self, obj):
        return f"{obj.serie}-{obj.numero:08d}"
    numero_completo.short_description = 'NÃºmero'


@admin.register(DetalleNotaCredito)
class DetalleNotaCreditoAdmin(admin.ModelAdmin):
    list_display = ['nota_credito', 'producto', 'cantidad', 'precio_unitario', 'subtotal']
    list_filter = ['nota_credito__tipo_nota']
    search_fields = ['producto__codigo', 'producto__descripcion']
