from rest_framework import viewsets
from apps.productos.models import Producto
from apps.productos.serializers import ProductoSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    filterset_fields = ['afecto_igv']
    search_fields = ['codigo', 'descripcion']