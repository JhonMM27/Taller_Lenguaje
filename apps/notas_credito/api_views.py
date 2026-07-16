"""
Backward-compatibility: re-exporta las views de NC desde la capa interfaces.
"""
from interfaces.api.nota_credito_views import NotaCreditoViewSet
from interfaces.api.serializers import (
    NotaCreditoSerializer,
    NotaCreditoCreateSerializer,
    DetalleNotaCreditoSerializer,
    DetalleComprobanteSerializer,
)

__all__ = [
    'NotaCreditoViewSet',
    'NotaCreditoSerializer',
    'NotaCreditoCreateSerializer',
    'DetalleNotaCreditoSerializer',
    'DetalleComprobanteSerializer',
]