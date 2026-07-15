"""
Entidades de dominio: Producto y CategoriaProducto.

Dataclass Python puro. CERO dependencias de Django.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ..excepciones import ReglaNegocioViolada


@dataclass
class CategoriaProducto:
    id: Optional[int]
    nombre: str
    descripcion: str = ""
    codigo_sunat: str = ""
    activo: bool = True


@dataclass
class Producto:
    id: Optional[int]
    descripcion: str
    precio_unitario: Decimal
    unidad_medida: str = "NIU"
    afecto_igv: bool = True
    cod_tipo_afectacion: str = "10"
    codigo: Optional[str] = None
    tipo_operacion: str = "GRAVADA"
    categoria_id: Optional[int] = None
    categoria: Optional["CategoriaProducto"] = None
    activo: bool = True

    def __post_init__(self) -> None:
        if self.precio_unitario < 0:
            raise ReglaNegocioViolada(
                "El precio unitario no puede ser negativo"
            )

    @property
    def precio_con_igv(self) -> Decimal:
        """Precio unitario incluyendo IGV (referencial, IGV=18%)."""
        if not self.afecto_igv:
            return self.precio_unitario
        return self.precio_unitario * Decimal("1.18")