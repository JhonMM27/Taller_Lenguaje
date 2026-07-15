"""Entidades del dominio: dataclasses Python puras (sin Django)."""
from .comprobante import (
    Comprobante,
    DetalleComprobante,
    SerieComprobante,
)
from .nota_credito import NotaCredito, DetalleNotaCredito
from .cliente import Cliente
from .producto import Producto, CategoriaProducto
from .empresa import Empresa

__all__ = [
    "Comprobante",
    "DetalleComprobante",
    "SerieComprobante",
    "NotaCredito",
    "DetalleNotaCredito",
    "Cliente",
    "Producto",
    "CategoriaProducto",
    "Empresa",
]