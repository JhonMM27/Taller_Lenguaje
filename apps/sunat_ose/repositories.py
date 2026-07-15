"""
Backward-compatibility: re-exporta el repositorio de log SUNAT.
"""
from infraestructura.persistencia import (
    DjangoLogSunatRepository as LogSunatRepositoryDjango,
)

__all__ = ['LogSunatRepositoryDjango']