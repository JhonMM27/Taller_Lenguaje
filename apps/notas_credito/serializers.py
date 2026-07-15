"""
Backward-compatibility: re-exporta serializers desde la capa interfaces.
"""
from interfaces.api.serializers import (
    NotaCreditoSerializer,
    NotaCreditoCreateSerializer,
    DetalleNotaCreditoSerializer,
)

__all__ = [
    'NotaCreditoSerializer',
    'NotaCreditoCreateSerializer',
    'DetalleNotaCreditoSerializer',
]