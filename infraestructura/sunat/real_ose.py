"""
Adaptador real del OSE.

Implementa IOSEService. Usa zeep con WSDL local para comunicarse con SUNAT/OSE.
El WSDL local se usa para evitar dependencias de red en la inicialización y
para resolver los imports relativos (billService_ns1.wsdl) correctamente.

Importante:
    - WSDL se carga desde archivo local (no se descarga de la URL remota).
    - SUNAT requiere credenciales en formato RUC-USUARIO.
    - El endpoint SOAP se sobreescribe a la URL real de SUNAT/OSE.
"""
from __future__ import annotations

import base64
import logging
import os
import pathlib
from typing import Optional

# pyrefly: ignore [missing-import]
from zeep import Client, Settings
# pyrefly: ignore [missing-import]
from zeep.transports import Transport
# pyrefly: ignore [missing-import]
from zeep.wsse.username import UsernameToken

logger = logging.getLogger(__name__)


class RealOSEAdapter:
    """Adaptador real del OSE via SOAP (zeep) usando WSDL local."""

    def __init__(self, wsdl_url: str, usuario: str, password: str, ruc: str) -> None:
        # wsdl_url en realidad es la URL del endpoint SOAP (no la URL del WSDL).
        self.service_url = wsdl_url
        self.usuario = usuario
        self.password = password
        self.ruc = ruc
        self._client = None

    def _get_client(self) -> Client:
        if self._client is None:
            from django.conf import settings as django_settings

            # Cargar WSDL local para evitar problemas al intentar descargar
            # la URL remota (que devuelve 500 al no ser un WSDL descargable).
            base_dir = getattr(django_settings, 'BASE_DIR', os.getcwd())
            wsdl_path = os.path.join(str(base_dir), 'wsdl', 'billService.wsdl')

            # Zeep necesita un URI file:/// (no un path Windows directo) para
            # resolver los imports relativos del WSDL (billService_ns1.wsdl).
            wsdl_uri = pathlib.Path(wsdl_path).as_uri()

            # SUNAT requiere autenticacion en formato RUC-USUARIO
            username = f"{self.ruc}-{self.usuario}"
            wsse = UsernameToken(username, self.password)

            transport = Transport(timeout=60)
            zeep_settings = Settings(strict=False, xml_huge_tree=True)

            logger.info(f"[RealOSE] Cargando WSDL local: {wsdl_path}")
            logger.info(f"[RealOSE] Endpoint SOAP: {self.service_url}")
            logger.info(f"[RealOSE] Usuario: {username}")

            self._client = Client(
                wsdl=wsdl_uri,  # <- URI, no path
                wsse=wsse,
                transport=transport,
                settings=zeep_settings,
            )
            logger.info(
                f"[RealOSE] Cliente OSE inicializado. "
                f"Servicios: {list(self._client.wsdl.services.keys())}"
            )

            # Sobreescribir el endpoint al URL real de SUNAT/OSE
            if self.service_url:
                self._client.service._binding_options['address'] = self.service_url
                logger.info(f"[RealOSE] Endpoint sobreescrito a: {self.service_url}")

        return self._client

    def send_bill(self, file_content, file_name: str) -> dict:
        """
        Envia un comprobante individual al OSE via SOAP sendBill.

        Args:
            file_content: ZIP (bytes o str base64).
            file_name: nombre del archivo ZIP con formato SUNAT.

        Returns:
            dict con status, applicationResponse, faultcode, faultstring.
        """
        logger.info(f"[RealOSE] Enviando comprobante: {file_name}")
        try:
            client = self._get_client()

            # Acepta bytes o base64 str
            zip_bytes = (
                base64.b64decode(file_content)
                if isinstance(file_content, str)
                else file_content
            )

            response = client.service.sendBill(
                fileName=file_name,
                contentFile=zip_bytes,
            )

            return {
                'status': 0,
                'applicationResponse': (
                    base64.b64encode(response).decode('utf-8')
                    if response else None
                ),
                'faultcode': None,
                'faultstring': None,
            }
        except Exception as e:
            logger.error(f"[RealOSE] Error enviando a OSE: {str(e)}")
            return {
                'status': -1,
                'ticket': None,
                'faultcode': getattr(e, 'code', 'ERROR'),
                'faultstring': getattr(e, 'message', str(e)),
            }

    def get_status(self, ticket: str) -> dict:
        try:
            client = self._get_client()
            response = client.service.getStatus(ticket=ticket)
            return {
                'status': (
                    response.statusCode
                    if hasattr(response, 'statusCode') else 0
                ),
                'ticket': ticket,
                'faultcode': None,
                'faultstring': None,
            }
        except Exception as e:
            logger.error(f"[RealOSE] Error consultando ticket: {str(e)}")
            return {
                'status': -1,
                'ticket': ticket,
                'faultcode': getattr(e, 'code', 'ERROR'),
                'faultstring': getattr(e, 'message', str(e)),
            }

    def get_status_cdr(self, ticket: str) -> dict:
        try:
            client = self._get_client()
            response = client.service.getStatusCdr(ticket=ticket)
            return {
                'status': 0,
                'cdrContent': (
                    response.content
                    if hasattr(response, 'content') else None
                ),
                'faultcode': None,
                'faultstring': None,
            }
        except Exception as e:
            logger.error(f"[RealOSE] Error consultando CDR: {str(e)}")
            return {
                'status': -1,
                'ticket': ticket,
                'faultcode': getattr(e, 'code', 'ERROR'),
                'faultstring': getattr(e, 'message', str(e)),
            }

    def send_pack(self, file_content, file_name: str) -> dict:
        """Envia un lote (asincrono) via sendPack."""
        try:
            client = self._get_client()
            zip_bytes = (
                base64.b64decode(file_content)
                if isinstance(file_content, str)
                else file_content
            )
            response = client.service.sendPack(
                fileName=file_name,
                contentFile=zip_bytes,
            )
            return {
                'status': 0,
                'ticket': response if isinstance(response, str) else None,
                'faultcode': None,
                'faultstring': None,
            }
        except Exception as e:
            logger.error(f"[RealOSE] Error enviando lote: {str(e)}")
            return {
                'status': -1,
                'ticket': None,
                'faultcode': getattr(e, 'code', 'ERROR'),
                'faultstring': getattr(e, 'message', str(e)),
            }