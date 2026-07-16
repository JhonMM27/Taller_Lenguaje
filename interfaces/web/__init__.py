"""Interfaces web (templates Django)."""
from .comprobante_web import (
    lista_comprobantes,
    crear_comprobante,
    detalle_comprobante,
    emitir_comprobante,
    reenviar_comprobante,
)

__all__ = [
    "lista_comprobantes",
    "crear_comprobante",
    "detalle_comprobante",
    "emitir_comprobante",
    "reenviar_comprobante",
]