"""
ViewSets de DRF para notas de credito.
"""
from __future__ import annotations

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.comprobantes.models import Comprobante, DetalleComprobante
from apps.notas_credito.models import NotaCredito
from dominio.excepciones import DomainError
from interfaces.container import (
    get_nota_credito_service,
    get_sunat_service,
)
from interfaces.api.serializers import (
    NotaCreditoCreateSerializer,
    NotaCreditoSerializer,
)

logger = logging.getLogger(__name__)


class NotaCreditoViewSet(viewsets.ModelViewSet):
    """ViewSet delgado: solo delega al servicio de dominio."""

    queryset = NotaCredito.objects.all()
    serializer_class = NotaCreditoSerializer
    filterset_fields = ['estado', 'tipo_nota', 'tipo_nc']

    def get_queryset(self):
        qs = NotaCredito.activos.select_related(
            'comprobante_referencia',
            'comprobante_referencia__cliente',
        ).all()
        user = self.request.user
        if user and user.is_authenticated:
            try:
                perfil = user.perfil
                if perfil.rol != 'ADMIN' and perfil.empresa:
                    qs = qs.filter(
                        comprobante_referencia__empresa=perfil.empresa
                    )
            except AttributeError:
                pass
        return qs.order_by('-fecha', '-creado_en')

    def get_serializer_class(self):
        if self.action == 'create':
            return NotaCreditoCreateSerializer
        return NotaCreditoSerializer

    def create(self, request, *args, **kwargs):
        input_ser = NotaCreditoCreateSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data
        service = get_nota_credito_service()
        creado_por_id = (
            request.user.id if request.user.is_authenticated else None
        )
        nota = service.emitir(
            comprobante_referencia_id=data['comprobante_id'],
            tipo_nc=data['tipo_nc'],
            tipo_nota=data['tipo_nota'],
            descripcion=data.get('descripcion', ''),
            detalles_data=list(data.get('detalles', []) or []),
            creado_por_id=creado_por_id,
        )
        modelo = NotaCredito.objects.select_related(
            'comprobante_referencia',
            'comprobante_referencia__cliente',
        ).get(pk=nota.id)
        return Response(
            NotaCreditoSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Envia la NC al OSE/SUNAT."""
        service = get_sunat_service()
        try:
            resultado = service.enviar_nota_credito(nota_id=int(pk))
        except DomainError:
            raise
        return Response(resultado)

    def destroy(self, request, *args, **kwargs):
        nota = self.get_object()
        service = get_nota_credito_service()
        usuario_id = (
            request.user.id if request.user.is_authenticated else None
        )
        service.eliminar(nota_id=nota.pk, usuario_id=usuario_id)
        return Response(status=status.HTTP_204_NO_CONTENT)