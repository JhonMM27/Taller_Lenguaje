from rest_framework import serializers as drf_serializers
from apps.productos.models import Producto, CategoriaProducto


class CategoriaProductoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = '__all__'


class ProductoSerializer(drf_serializers.ModelSerializer):
    categoria_nombre = drf_serializers.CharField(source='categoria.nombre', read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'