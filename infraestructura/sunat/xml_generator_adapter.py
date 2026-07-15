"""
Adaptador del generador de XML UBL 2.1.

Implementa el Protocol interno _XmlGenerator que espera el SunatEnvioService.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class XmlGeneratorAdapter:
    """Genera XML UBL 2.1 desde un comprobante o NC."""

    def generar(self, comprobante) -> str:
        try:
            from apps.sunat_ose.xml_generator import generar_xml_ubl
            return generar_xml_ubl(comprobante)
        except Exception as exc:
            logger.exception("Error generando XML de comprobante")
            raise

    def generar_nota_credito(self, nota) -> str:
        try:
            from apps.sunat_ose.xml_generator import generar_xml_nota_credito
            return generar_xml_nota_credito(nota)
        except Exception as exc:
            logger.exception("Error generando XML de NC")
            raise