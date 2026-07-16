from rest_framework import serializers as drf_serializers
# pyrefly: ignore [missing-import]
from apps.productos.models import Producto, CategoriaProducto


class CategoriaProductoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = CategoriaProducto
        fields = '__all__'

    def to_internal_value(self, data):
        """Normaliza el checkbox 'activo' desde el form HTML.

        Los checkboxes HTML solo envian el valor cuando estan marcados.
        Si no llega, asumimos False (categoria inactiva).
        Si llega como 'on'/'true'/'1', lo convertimos a True.
        """
        if hasattr(data, 'dict'):
            normalized_data = data.dict()
        else:
            normalized_data = dict(data)

        if 'activo' in normalized_data:
            val = normalized_data['activo']
            if isinstance(val, bool):
                pass
            elif val in ('on', 'true', '1', True):
                normalized_data['activo'] = True
            else:
                normalized_data['activo'] = False
        else:
            normalized_data['activo'] = False

        return super().to_internal_value(normalized_data)


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