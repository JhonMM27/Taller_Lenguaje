"""
Backward-compatibility: re-exporta services y serializers de interfaces.
"""
from interfaces.api.serializers import (
    ComprobanteSerializer,
    ComprobanteCreateSerializer,
    DetalleComprobanteSerializer,
    LogEnvioSUNATSerializer,
)

__all__ = [
    'ComprobanteSerializer',
    'ComprobanteCreateSerializer',
    'DetalleComprobanteSerializer',
    'LogEnvioSUNATSerializer',
]