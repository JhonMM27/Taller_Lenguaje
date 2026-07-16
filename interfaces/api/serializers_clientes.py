"""Serializers de clientes y productos para la API."""
from rest_framework import serializers

from apps.clientes.models import Cliente
from apps.productos.models import Producto


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            'id', 'tipo_doc', 'num_doc', 'razon_social', 'codigo',
            'direccion', 'telefono', 'email', 'ubigeo',
            'creado_en', 'actualizado_en',
        ]


class ClienteCreateSerializer(serializers.Serializer):
    tipo_doc = serializers.ChoiceField(choices=['1', '4', '6', '7', 'A'])
    num_doc = serializers.CharField(max_length=15)
    razon_social = serializers.CharField(max_length=200)
    codigo = serializers.CharField(max_length=10, required=False, allow_blank=True)
    direccion = serializers.CharField(required=False, allow_blank=True)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    ubigeo = serializers.CharField(max_length=6, required=False, allow_blank=True)


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