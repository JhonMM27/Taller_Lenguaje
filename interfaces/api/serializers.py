"""
Serializers para la capa API.

Los serializers SOLO se encargan de:
  - Validar tipos de datos de entrada.
  - Construir diccionarios de salida para JSON.

NO contienen logica de negocio. Toda la logica va al servicio de dominio.
"""
from __future__ import annotations

from rest_framework import serializers

from apps.comprobantes.models import (
    Comprobante,
    DetalleComprobante,
    LogEnvioSUNAT,
)
from apps.notas_credito.models import NotaCredito, DetalleNotaCredito


# ============================================================
# Detalle Comprobante
# ============================================================

class DetalleComprobanteSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleComprobante
        fields = [
            'id', 'producto', 'producto_codigo', 'producto_descripcion',
            'cantidad', 'precio_unitario', 'descuento',
            'afecto_igv', 'cod_tipo_afectacion',
            'igv_linea', 'subtotal',
        ]


class DetalleComprobanteInputSerializer(serializers.Serializer):
    """Schema de entrada para una linea de detalle."""
    producto_id = serializers.IntegerField()
    cantidad = serializers.DecimalField(max_digits=12, decimal_places=4)
    precio_unitario = serializers.DecimalField(
        max_digits=12, decimal_places=4, required=False, allow_null=True
    )
    descuento = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, default=0
    )


# ============================================================
# Comprobante
# ============================================================

class ComprobanteSerializer(serializers.ModelSerializer):
    detalles = DetalleComprobanteSerializer(many=True, read_only=True)
    cliente_nombre = serializers.CharField(source='cliente.razon_social', read_only=True)
    empresa_ruc = serializers.CharField(source='empresa.ruc', read_only=True)

    class Meta:
        model = Comprobante
        fields = [
            'id', 'empresa', 'empresa_ruc', 'cliente', 'cliente_nombre',
            'serie', 'numero', 'fecha', 'tipo', 'estado',
            'subtotal', 'igv', 'total', 'xml_firmado', 'detalles',
            'creado_en', 'actualizado_en',
        ]


class ComprobanteCreateSerializer(serializers.Serializer):
    """Schema de entrada para crear un comprobante. NO logica de negocio."""
    empresa_id = serializers.IntegerField()
    cliente_id = serializers.IntegerField()
    fecha = serializers.DateField()
    tipo = serializers.ChoiceField(choices=['01', '03'])
    detalles = serializers.ListField(
        child=DetalleComprobanteInputSerializer(), allow_empty=False
    )


class ComprobanteReenviarSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True)


# ============================================================
# Log SUNAT
# ============================================================

class LogEnvioSUNATSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEnvioSUNAT
        fields = '__all__'


# ============================================================
# Nota de Credito
# ============================================================

class DetalleNotaCreditoSerializer(serializers.ModelSerializer):
    producto_codigo = serializers.CharField(source='producto.codigo', read_only=True)
    producto_descripcion = serializers.CharField(source='producto.descripcion', read_only=True)

    class Meta:
        model = DetalleNotaCredito
        fields = [
            'id', 'producto', 'producto_codigo', 'producto_descripcion',
            'cantidad', 'precio_unitario', 'descuento',
            'afecto_igv', 'cod_tipo_afectacion',
            'igv_linea', 'subtotal',
        ]


class NotaCreditoSerializer(serializers.ModelSerializer):
    detalles = DetalleNotaCreditoSerializer(many=True, read_only=True)
    comprobante_numero = serializers.CharField(
        source='comprobante_referencia.numero', read_only=True
    )

    class Meta:
        model = NotaCredito
        fields = '__all__'


class NotaCreditoCreateSerializer(serializers.Serializer):
    comprobante_id = serializers.IntegerField()
    tipo_nc = serializers.ChoiceField(choices=['NC', 'NCD'])
    tipo_nota = serializers.CharField(max_length=2)
    descripcion = serializers.CharField(required=False, allow_blank=True)
    detalles = serializers.ListField(
        child=DetalleComprobanteInputSerializer(), required=False
    )