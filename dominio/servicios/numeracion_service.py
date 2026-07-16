"""
Servicio de dominio: NumeracionService.

Garantiza correlativos sin saltos. La implementacion concreta de la
atomicidad depende del adaptador (en Django se usa select_for_update).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..excepciones import SerieNoEncontrada
from ..puertos.repositorios import ISerieComprobanteRepository


@runtime_checkable
class _NumeracionRepo(Protocol):
    """Subset del repo de series necesario para numeracion."""

    def siguiente_correlativo(
        self, empresa_id: int, tipo: str
    ) -> tuple:  # (SerieComprobante, int)
        ...


class NumeracionService:
    """Caso de uso: reservar el siguiente numero correlativo."""

    def __init__(self, series_repo: ISerieComprobanteRepository) -> None:
        self._series = series_repo

    def siguiente(
        self, empresa_id: int, tipo: str
    ) -> tuple:
        """Devuelve (serie, numero) para el siguiente comprobante."""
        try:
            return self._series.siguiente_correlativo(empresa_id, tipo)
        except Exception as exc:
            raise SerieNoEncontrada(
                f"No se pudo obtener numeracion para empresa={empresa_id} tipo={tipo}: {exc}"
            ) from exc