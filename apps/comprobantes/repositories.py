"""
Backward-compatibility: re-exporta el repositorio hexagonal.

Las views que usan `ComprobanteRepositoryDjango` siguen funcionando porque
este archivo re-exporta el adaptador de `infraestructura`.
"""
from infraestructura.persistencia import (
    DjangoComprobanteRepository as ComprobanteRepositoryDjango,
)
from infraestructura.persistencia import (
    DjangoSerieComprobanteRepository as SerieRepositoryDjango,
)

__all__ = ['ComprobanteRepositoryDjango', 'SerieRepositoryDjango']