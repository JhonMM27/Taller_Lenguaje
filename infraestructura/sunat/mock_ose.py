"""
Adaptador mock del OSE.

Implementa IOSEService. Simula el comportamiento del OSE real
para desarrollo y testing.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from typing import Optional

from dominio.excepciones import EnvioSunatFallido


logger = logging.getLogger(__name__)


class MockOSEAdapter:
    """Adaptador que simula un OSE para desarrollo y tests."""

    def __init__(self, tasa_rechazo: float = 0.0) -> None:
        self.tasa_rechazo = tasa_rechazo
        self._tickets: dict[str, dict] = {}

    def send_bill(self, file_content: bytes, file_name: str) -> dict:
        """Simula el envio de un comprobante."""
        import random
        if random.random() < self.tasa_rechazo:
            return {
                "status": 99,
                "faultstring": "Error simulado de OSE mock",
            }
        ticket = str(uuid.uuid4())
        # Crea un CDR mock en base64 (zip vacio codificado).
        cdr_mock = base64.b64encode(b"MOCK-CDR-CONTENT").decode("utf-8")
        self._tickets[ticket] = {
            "status": 0,
            "cdr": cdr_mock,
        }
        return {
            "status": 0,
            "ticket": ticket,
            "applicationResponse": cdr_mock,
            "faultstring": None,
        }

    def get_status(self, ticket: str) -> dict:
        if ticket in self._tickets:
            return self._tickets[ticket]
        return {"status": 0, "faultstring": None}

    def get_status_cdr(self, ticket: str) -> dict:
        if ticket in self._tickets:
            return {"cdrContent": self._tickets[ticket]["cdr"]}
        return {"cdrContent": ""}