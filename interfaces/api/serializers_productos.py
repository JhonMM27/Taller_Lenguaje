"""Serializers de productos."""
from rest_framework import serializers

from apps.productos.models import Producto


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = [
            'id', 'codigo', 'descripcion', 'unidad_medida',
            'precio_unitario', 'afecto_igv', 'cod_tipo_afectacion',
            'categoria', 'tipo_operacion',
            'creado_en', 'actualizado_en',
        ]


class ProductoCreateSerializer(serializers.Serializer):
    descripcion = serializers.CharField(max_length=500)
    precio_unitario = serializers.DecimalField(max_digits=12, decimal_places=2)
    unidad_medida = serializers.CharField(
        max_length=10, required=False, default='NIU'
    )
    afecto_igv = serializers.BooleanField(required=False, default=True)
    cod_tipo_afectacion = serializers.CharField(
        max_length=10, required=False, default='10'
    )
    tipo_operacion = serializers.ChoiceField(
        choices=['GRAVADA', 'EXONERADA', 'INAFECTA', 'GRATUITA', 'EXPORTACION'],
        required=False, default='GRAVADA',
    )
    categoria_id = serializers.IntegerField(required=False, allow_null=True)