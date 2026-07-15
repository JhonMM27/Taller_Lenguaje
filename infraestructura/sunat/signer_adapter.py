"""
Adaptador del firmador de XML.

Implementa IXmlSigner del dominio. Usa el modulo `apps.sunat_ose.firmar`
que ya tiene la logica con signxml.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class XmlSignerAdapter:
    """Firma XML UBL 2.1 usando el certificado de la empresa."""

    def firmar(self, xml_content: str, empresa_id: int) -> str:
        try:
            from apps.sunat_ose.firmar import firmar_xml
            resultado = firmar_xml(xml_content, empresa_id=empresa_id)
            if isinstance(resultado, bytes):
                return resultado.decode("utf-8")
            return resultado
        except Exception as exc:
            logger.exception("Error firmando XML para empresa=%s", empresa_id)
            raise