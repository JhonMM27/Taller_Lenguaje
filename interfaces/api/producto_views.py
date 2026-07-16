"""
ViewSets de DRF para productos.
"""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.productos.models import Producto
from interfaces.container import get_producto_service
from interfaces.api.serializers_productos import (
    ProductoCreateSerializer,
    ProductoSerializer,
)


class ProductoViewSet(viewsets.ModelViewSet):
    """ViewSet delgado: solo delega al servicio de dominio."""

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer

    def get_queryset(self):
        return Producto.activos.all().order_by('codigo')

    def get_serializer_class(self):
        if self.action == 'create':
            return ProductoCreateSerializer
        return ProductoSerializer

    def create(self, request, *args, **kwargs):
        input_ser = ProductoCreateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        service = get_producto_service()
        producto = service.crear(input_ser.validated_data)
        modelo = Producto.objects.get(pk=producto.id)
        return Response(
            ProductoSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        producto = self.get_object()
        service = get_producto_service()
        usuario_id = (
            request.user.id if request.user.is_authenticated else None
        )
        service.eliminar(producto_id=producto.pk, usuario_id=usuario_id)
        return Response(status=status.HTTP_204_NO_CONTENT)