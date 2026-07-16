"""
ViewSets de DRF para clientes.
"""
from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.clientes.models import Cliente
from dominio.excepciones import DomainError
from interfaces.container import get_cliente_service
from interfaces.api.serializers_clientes import (
    ClienteCreateSerializer,
    ClienteSerializer,
)


class ClienteViewSet(viewsets.ModelViewSet):
    """ViewSet delgado: solo delega al servicio de dominio."""

    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer

    def get_queryset(self):
        return Cliente.activos.all().order_by('razon_social')

    def get_serializer_class(self):
        if self.action == 'create':
            return ClienteCreateSerializer
        return ClienteSerializer

    def create(self, request, *args, **kwargs):
        input_ser = ClienteCreateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        service = get_cliente_service()
        cliente = service.crear(input_ser.validated_data)
        modelo = Cliente.objects.get(pk=cliente.id)
        return Response(
            ClienteSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        cliente = self.get_object()
        service = get_cliente_service()
        usuario_id = (
            request.user.id if request.user.is_authenticated else None
        )
        try:
            service.eliminar(cliente_id=cliente.pk, usuario_id=usuario_id)
        except DomainError:
            raise
        return Response(status=status.HTTP_204_NO_CONTENT)