from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.productos.models import Producto
from apps.productos.serializers import ProductoSerializer
from apps.productos.services import ProductoService


class ProductoViewSet(viewsets.ModelViewSet):
    serializer_class = ProductoSerializer
    filterset_fields = ['afecto_igv']
    search_fields = ['codigo', 'descripcion']

    def get_queryset(self):
        return Producto.activos.all()

    def create(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            producto = ProductoService.crear(serializer.validated_data, usuario=request.user)
            return Response(ProductoSerializer(producto).data, status=status.HTTP_201_CREATED)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            producto = ProductoService.actualizar(instance.id, serializer.validated_data)
            return Response(ProductoSerializer(producto).data)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        instance = self.get_object()
        try:
            ProductoService.eliminar(instance.id, usuario=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)