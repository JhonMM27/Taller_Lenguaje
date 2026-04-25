from django.contrib import admin
from .models import SerieComprobante, Comprobante, DetalleComprobante, LogEnvioSUNAT


class DetalleInline(admin.TabularInline):
    model = DetalleComprobante
    extra = 1


@admin.register(SerieComprobante)
class SerieComprobanteAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'tipo', 'serie', 'correlativo_actual', 'activa']
    list_filter = ['empresa', 'tipo', 'activa']
    search_fields = ['serie']


@admin.register(Comprobante)
class ComprobanteAdmin(admin.ModelAdmin):
    list_display = ['numero_completo', 'empresa', 'cliente', 'fecha', 'total', 'estado']
    list_filter = ['estado', 'tipo', 'empresa']
    search_fields = ['numero', 'cliente__razon_social']
    inlines = [DetalleInline]
    readonly_fields = ['subtotal', 'igv', 'total', 'xml_firmado']

    def numero_completo(self, obj):
        return f"{obj.serie.serie}-{obj.numero:08d}"
    numero_completo.short_description = 'Número'


@admin.register(LogEnvioSUNAT)
class LogEnvioSUNATAdmin(admin.ModelAdmin):
    list_display = ['comprobante', 'fecha_envio', 'codigo_respuesta', 'estado_respuesta']
    list_filter = ['estado_respuesta', 'codigo_respuesta']
    search_fields = ['comprobante__numero']
    readonly_fields = ['fecha_envio']