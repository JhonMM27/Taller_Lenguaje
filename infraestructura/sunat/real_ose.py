"""
Adaptador real del OSE.

Implementa IOSEService. Usa zeep para comunicarse con el WSDL del OSE.
"""
from __future__ import annotations

import base64
import logging
from typing import Optional

from zeep import Client
from zeep.transports import Transport

logger = logging.getLogger(__name__)


class RealOSEAdapter:
    """Adaptador real del OSE via SOAP (zeep)."""

    def __init__(self, wsdl_url: str, usuario: str, password: str, ruc: str) -> None:
        self.wsdl_url = wsdl_url
        self.usuario = usuario
        self.password = password
        self.ruc = ruc
        self._client = None

    def _get_client(self) -> Client:
        if self._client is None:
            transport = Transport(timeout=30)
            self._client = Client(
                wsdl=self.wsdl_url,
                transport=transport,
            )
        return self._client

    def send_bill(self, file_content: bytes, file_name: str) -> dict:
        try:
            client = self._get_client()
            # El contenido llega como bytes (zip). Lo pasamos como base64.
            content_b64 = (
                file_content if isinstance(file_content, str)
                else base64.b64encode(file_content).decode("utf-8")
            )
            response = client.service.sendBill(
                fileName=file_name,
                contentFile=content_b64,
            )
            return {
                "status": 0,
                "ticket": getattr(response, "ticket", None),
                "applicationResponse": getattr(response, "applicationResponse", ""),
                "faultstring": None,
            }
        except Exception as exc:
            logger.exception("Error en sendBill real")
            return {
                "status": 99,
                "faultstring": str(exc),
            }

    def get_status(self, ticket: str) -> dict:
        try:
            client = self._get_client()
            response = client.service.getStatus(ticket=ticket)
            return {
                "status": int(getattr(response, "status", 0) or 0),
                "faultstring": getattr(response, "faultstring", None),
            }
        except Exception as exc:
            logger.exception("Error en getStatus real")
            return {"status": 99, "faultstring": str(exc)}

    def get_status_cdr(self, ticket: str) -> dict:
        try:
            client = self._get_client()
            response = client.service.getStatusCdr(ticket=ticket)
            return {
                "cdrContent": getattr(response, "cdrContent", ""),
            }
        except Exception as exc:
            logger.exception("Error en getStatusCdr real")
            return {"cdrContent": ""}