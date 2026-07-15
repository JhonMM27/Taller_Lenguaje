"""
Backward-compatibility: re-exporta las views hexagonales.

Las views originales vivian aqui. Ahora viven en
`interfaces/api/comprobante_views.py`. Este archivo solo re-exporta
para mantener compatibilidad con codigo viejo que pueda importarlas.
"""
from interfaces.api.comprobante_views import (
    ComprobanteViewSet,
    ComprobantePagination,
    LogEnvioSUNATViewSet,
)

__all__ = [
    'ComprobanteViewSet',
    'ComprobantePagination',
    'LogEnvioSUNATViewSet',
]