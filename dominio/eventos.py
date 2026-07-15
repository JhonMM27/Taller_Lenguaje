"""
Eventos del dominio.

Dataclasses inmutables que representan hechos del dominio. Los servicios
publican eventos, los handlers en otras capas reaccionan.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class DomainEvent:
    """Base de todos los eventos del dominio."""
    occurred_at: datetime = None

    def __post_init__(self) -> None:
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now())


@dataclass(frozen=True)
class ComprobanteCreado(DomainEvent):
    comprobante_id: int = 0
    empresa_id: int = 0
    tipo: str = ""
    numero: int = 0
    total: Decimal = Decimal("0")
    creado_por_id: Optional[int] = None


@dataclass(frozen=True)
class ComprobanteEmitido(DomainEvent):
    comprobante_id: int = 0
    empresa_id: int = 0
    xml_firmado: bool = False


    def __post_init__(self) -> None:
        if self.occurred_at is None:
            object.__setattr__(self, "occurred_at", datetime.now())


@dataclass(frozen=True)
class ComprobanteEnviado(DomainEvent):
    comprobante_id: int = 0
    ticket: Optional[str] = None
    es_mock: bool = False


@dataclass(frozen=True)
class ComprobanteAceptado(DomainEvent):
    comprobante_id: int = 0
    ticket: Optional[str] = None
    cdr_recibido: bool = False


@dataclass(frozen=True)
class ComprobanteRechazado(DomainEvent):
    comprobante_id: int = 0
    motivo: str = ""
    codigo_error: str = ""


@dataclass(frozen=True)
class ComprobanteReenviado(DomainEvent):
    comprobante_id: int = 0


@dataclass(frozen=True)
class ComprobanteEliminado(DomainEvent):
    comprobante_id: int = 0
    eliminado_por_id: Optional[int] = None


@dataclass(frozen=True)
class NotaCreditoEmitida(DomainEvent):
    nota_id: int = 0
    comprobante_referencia_id: int = 0
    importe: Decimal = Decimal("0")


@dataclass(frozen=True)
class NotaCreditoAceptada(DomainEvent):
    nota_id: int = 0
    ticket: Optional[str] = None


@dataclass(frozen=True)
class NotaCreditoRechazada(DomainEvent):
    nota_id: int = 0
    motivo: str = ""