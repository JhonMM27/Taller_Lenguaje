from rest_framework import serializers as drf_serializers
from apps.productos.models import Producto


class ProductoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'