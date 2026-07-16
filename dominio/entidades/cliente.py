"""
Entidad de dominio: Cliente.

Dataclass Python puro. CERO dependencias de Django.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..excepciones import DocumentoClienteInvalido


TIPOS_DOC_VALIDOS = ("0", "1", "4", "6", "7", "A")
LONGITUDES_DOC = {"1": 8, "6": 11}
TIPOS_DOC_EXTRANJEROS = ("0", "4", "7", "A")


@dataclass
class Cliente:
    """Cliente receptor de un comprobante electronico."""

    id: Optional[int]
    tipo_doc: str
    num_doc: str
    razon_social: str
    codigo: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    ubigeo: Optional[str] = None
    pais_codigo: str = "PE"
    activo: bool = True

    def __post_init__(self) -> None:
        self._validar_documento()
        self._validar_telefono()

    def _validar_documento(self) -> None:
        if self.tipo_doc not in TIPOS_DOC_VALIDOS:
            raise DocumentoClienteInvalido(
                f"Tipo de documento invalido: {self.tipo_doc}. "
                f"Validos: {TIPOS_DOC_VALIDOS}"
            )
        num = str(self.num_doc or "").strip()
        if not num:
            raise DocumentoClienteInvalido(
                "El numero de documento es obligatorio"
            )
        esperado = LONGITUDES_DOC.get(self.tipo_doc)
        if esperado and (not num.isdigit() or len(num) != esperado):
            nombres = {"1": "DNI", "4": "Carnet Extranjeria",
                       "6": "RUC", "7": "Pasaporte", "A": "Cedula"}
            raise DocumentoClienteInvalido(
                f"El {nombres.get(self.tipo_doc, self.tipo_doc)} debe tener "
                f"exactamente {esperado} digitos"
            )
        if self.tipo_doc in TIPOS_DOC_EXTRANJEROS:
            if len(num) > 15 or any(caracter.isspace() for caracter in num):
                raise DocumentoClienteInvalido(
                    "El documento extranjero debe tener hasta 15 caracteres y no contener espacios"
                )
        pais = str(self.pais_codigo or "PE").strip().upper()
        if len(pais) != 2 or not pais.isalpha():
            raise DocumentoClienteInvalido(
                "El pais debe usar un codigo ISO-3166 de dos letras"
            )
        self.pais_codigo = pais

    def _validar_telefono(self) -> None:
        if self.telefono and len(str(self.telefono).strip()) != 9:
            raise DocumentoClienteInvalido(
                "El telefono debe tener exactamente 9 digitos"
            )

    @property
    def es_persona_juridica(self) -> bool:
        return self.tipo_doc == "6"

    @property
    def es_persona_natural(self) -> bool:
        return self.tipo_doc != "6"
