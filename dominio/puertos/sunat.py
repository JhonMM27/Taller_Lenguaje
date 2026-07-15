"""
Contratos del dominio con servicios externos.

Estos Protocols definen la API que el dominio espera del mundo exterior
(SUNAT, firmador de XML, etc.). Los adaptadores en `infraestructura/sunat/`
y `infraestructura/xml/` los implementan.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IOSEService(Protocol):
    """Contrato con un OSE (Operador de Servicios Electronicos)."""

    def send_bill(self, file_content, file_name: str) -> dict:
        """Envia un comprobante (XML+ZIP) al OSE.

        Args:
            file_content: ZIP en bytes o base64 str.
            file_name: nombre del archivo ZIP con formato SUNAT.

        Returns:
            dict con al menos:
              - status: int (0 = exito, otros = error)
              - ticket: str opcional
              - applicationResponse: str base64 opcional
              - faultstring: str opcional
        """
        ...

    def get_status(self, ticket: str) -> dict:
        """Consulta el estado de un ticket en el OSE."""
        ...

    def get_status_cdr(self, ticket: str) -> dict:
        """Obtiene el CDR (constancia de recepcion) de un ticket."""
        ...

    def send_pack(self, file_content, file_name: str) -> dict:
        """Envia un lote de comprobantes (asincrono) via sendPack."""
        ...


@runtime_checkable
class IXmlSigner(Protocol):
    """Contrato para el firmador de XML."""

    def firmar(self, xml_content: str, empresa_id: int) -> str:
        """Firma un XML UBL 2.1 y devuelve el XML firmado."""
        ...


# Tasa de IGV por defecto (Peru). Puede sobreescribirse via configuracion.
IGV_TASA = 0.18