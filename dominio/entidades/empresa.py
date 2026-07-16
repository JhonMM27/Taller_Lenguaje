"""
Entidad de dominio: Empresa.

Dataclass Python puro. CERO dependencias de Django.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

from ..excepciones import DocumentoClienteInvalido


@dataclass
class Empresa:
    """Empresa emisora de comprobantes electronicos."""

    id: Optional[int]
    ruc: str
    razon_social: str
    nombre_comercial: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    regimen_tributario: str = "GENERAL"
    logo: Optional[str] = None
    codigo: Optional[str] = None
    activo: bool = True

    def __post_init__(self) -> None:
        self._validar_ruc()

    def _validar_ruc(self) -> None:
        if self.ruc and len(str(self.ruc)) != 11:
            raise DocumentoClienteInvalido("El RUC debe tener 11 digitos")
        if self.ruc and not str(self.ruc).isdigit():
            raise DocumentoClienteInvalido("El RUC solo debe contener digitos")

    @property
    def tiene_certificado_activo(self) -> bool:
        """Placeholder: la verificacion real la hace el repositorio."""
        return False