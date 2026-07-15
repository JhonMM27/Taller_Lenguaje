from rest_framework import serializers as drf_serializers
# pyrefly: ignore [missing-import]
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

    def to_internal_value(self, data):
        # Convertir a un diccionario normal de Python para evitar las listas internas de QueryDict
        if hasattr(data, 'dict'):
            normalized_data = data.dict()
        else:
            normalized_data = dict(data)

        # Normalizar el checkbox afecto_igv
        if 'afecto_igv' in normalized_data:
            val = normalized_data['afecto_igv']
            if val in ['on', 'true', '1', True]:
                normalized_data['afecto_igv'] = True
            else:
                normalized_data['afecto_igv'] = False
        else:
            normalized_data['afecto_igv'] = False

        return super().to_internal_value(normalized_data)