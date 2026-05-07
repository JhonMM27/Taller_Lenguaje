"""
SUNAT OSE Client - Para entorno BETA/DESARROLLO
Usa requests directo para SOAP (no zeep) para evitar problemas de auth en imports del WSDL.
"""

import logging
import os
import base64
from django.conf import settings

logger = logging.getLogger(__name__)


class OSEClient:
    """Cliente SOAP usando requests directo para evitar problemas de auth con zeep"""

    def __init__(self, wsdl_url=None, ruc=None, usuario=None, password=None):
        self.wsdl_url = wsdl_url or os.getenv('SUNAT_OSE_WSDL', '')
        self.ruc = ruc or os.getenv('SUNAT_OSE_RUC', '')
        self.usuario = usuario or os.getenv('SUNAT_OSE_USUARIO', '')
        self.password = password or os.getenv('SUNAT_OSE_PASSWORD', '')

    @property
    def auth(self):
        from requests.auth import HTTPBasicAuth
        return HTTPBasicAuth(self.ruc + '-' + self.usuario, self.password)

    def send_bill(self, zip_content, file_name):
        """Envía comprobante al OSE usando SOAP directo"""
        import requests

        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
         <wsse:UsernameToken>
            <wsse:Username>{self.ruc}-{self.usuario}</wsse:Username>
            <wsse:Password>{self.password}</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <ser:sendBill>
         <ser:fileName>{file_name}</ser:fileName>
         <ser:zipContent>{zip_content}</ser:zipContent>
      </ser:sendBill>
   </soapenv:Body>
</soapenv:Envelope>'''

        logger.info(f"Enviando comprobante: {file_name}")

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'sendBill'
        }

        try:
            response = requests.post(
                self.wsdl_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=60
            )

            if response.status_code == 200:
                return self._parse_response(response.text, file_name)
            else:
                logger.error(f"Error HTTP {response.status_code}: {response.text}")
                return {
                    'status': -1,
                    'ticket': None,
                    'faultcode': str(response.status_code),
                    'faultstring': f"HTTP Error: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error enviando a OSE: {str(e)}")
            return {
                'status': -1,
                'ticket': None,
                'faultcode': 'ERROR',
                'faultstring': str(e)
            }

    def _parse_response(self, xml_response, file_name):
        """Parsea la respuesta SOAP"""
        from xml.etree import ElementTree as ET

        try:
            root = ET.fromstring(xml_response)

            ns = {
                'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
                'ns2': 'http://service.sunat.gob.pe'
            }

            status = root.find('.//ns2:status', ns) or root.find('.//status', ns)
            ticket = root.find('.//ns2:ticket', ns) or root.find('.//ticket', ns)
            faultstring = root.find('.//faultstring', ns)
            faultcode = root.find('.//faultcode', ns)

            status_val = int(status.text) if status is not None else -1
            ticket_val = ticket.text if ticket is not None else None
            faultstring_val = faultstring.text if faultstring is not None else None
            faultcode_val = faultcode.text if faultcode is not None else None

            logger.info(f"Respuesta OSE - status: {status_val}, ticket: {ticket_val}")

            return {
                'status': status_val,
                'ticket': ticket_val,
                'faultcode': faultcode_val,
                'faultstring': faultstring_val
            }
        except Exception as e:
            logger.error(f"Error parseando respuesta: {str(e)}")
            return {
                'status': -1,
                'ticket': None,
                'faultcode': 'PARSE_ERROR',
                'faultstring': f"Error parseando respuesta: {str(e)}"
            }

    def get_status(self, ticket):
        """Consulta estado de ticket"""
        import requests

        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
         <wsse:UsernameToken>
            <wsse:Username>{self.ruc}-{self.usuario}</wsse:Username>
            <wsse:Password>{self.password}</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <ser:getStatus>
         <ser:ticket>{ticket}</ser:ticket>
      </ser:getStatus>
   </soapenv:Body>
</soapenv:Envelope>'''

        logger.info(f"Consultando ticket: {ticket}")

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'getStatus'
        }

        try:
            response = requests.post(
                self.wsdl_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=60
            )

            if response.status_code == 200:
                return self._parse_response(response.text, None)
            else:
                return {
                    'status': -1,
                    'ticket': ticket,
                    'faultcode': str(response.status_code),
                    'faultstring': f"HTTP Error: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error consultando ticket: {str(e)}")
            return {
                'status': -1,
                'ticket': ticket,
                'faultcode': 'ERROR',
                'faultstring': str(e)
            }

    def get_status_cdr(self, ticket):
        """Consulta CDR por ticket"""
        import requests

        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
         <wsse:UsernameToken>
            <wsse:Username>{self.ruc}-{self.usuario}</wsse:Username>
            <wsse:Password>{self.password}</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <ser:getStatusCdr>
         <ser:ticket>{ticket}</ser:ticket>
      </ser:getStatusCdr>
   </soapenv:Body>
</soapenv:Envelope>'''

        logger.info(f"Consultando CDR para ticket: {ticket}")

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'getStatusCdr'
        }

        try:
            response = requests.post(
                self.wsdl_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=60
            )

            if response.status_code == 200:
                return self._parse_response(response.text, None)
            else:
                return {
                    'status': -1,
                    'ticket': ticket,
                    'faultcode': str(response.status_code),
                    'faultstring': f"HTTP Error: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error consultando CDR: {str(e)}")
            return {
                'status': -1,
                'ticket': ticket,
                'faultcode': 'ERROR',
                'faultstring': str(e)
            }

    def send_pack(self, zip_content, file_name):
        """Envía lote de comprobantes"""
        import requests

        soap_body = f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://service.sunat.gob.pe">
   <soapenv:Header>
      <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
         <wsse:UsernameToken>
            <wsse:Username>{self.ruc}-{self.usuario}</wsse:Username>
            <wsse:Password>{self.password}</wsse:Password>
         </wsse:UsernameToken>
      </wsse:Security>
   </soapenv:Header>
   <soapenv:Body>
      <ser:sendPack>
         <ser:fileName>{file_name}</ser:fileName>
         <ser:zipContent>{zip_content}</ser:zipContent>
      </ser:sendPack>
   </soapenv:Body>
</soapenv:Envelope>'''

        logger.info(f"Enviando lote: {file_name}")

        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'sendPack'
        }

        try:
            response = requests.post(
                self.wsdl_url,
                data=soap_body.encode('utf-8'),
                headers=headers,
                auth=self.auth,
                timeout=120
            )

            if response.status_code == 200:
                return self._parse_response(response.text, file_name)
            else:
                return {
                    'status': -1,
                    'ticket': None,
                    'faultcode': str(response.status_code),
                    'faultstring': f"HTTP Error: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"Error enviando lote: {str(e)}")
            return {
                'status': -1,
                'ticket': None,
                'faultcode': 'ERROR',
                'faultstring': str(e)
            }


class MockOSEClient:
    """Cliente MOCK para desarrollo local"""

    def __init__(self, *args, **kwargs):
        pass

    def send_bill(self, zip_content, file_name):
        import random
        import uuid
        import time

        time.sleep(random.uniform(0.5, 1.5))

        if random.random() < 0.9:
            return {
                'status': 0,
                'ticket': f"MOCK-{uuid.uuid4().hex[:10].upper()}",
                'faultcode': None,
                'faultstring': None
            }
        else:
            return {
                'status': 99,
                'ticket': None,
                'faultcode': '2000',
                'faultstring': random.choice([
                    "Error de negocio: Numeración duplicada",
                    "Error de estructura: Formato inválido de XML",
                    "Error de datos: RUC no existe en padrón",
                    "Error de validación: Fecha fuera de rango",
                ])
            }

    def get_status(self, ticket):
        import random
        import time

        time.sleep(random.uniform(0.3, 1.0))

        return {
            'status': 0,
            'ticket': ticket,
            'faultcode': None,
            'faultstring': None
        }

    def get_status_cdr(self, ticket):
        import random
        import time

        time.sleep(random.uniform(0.3, 1.0))

        mock_cdr = b'RUF== mock CDR content for development'

        return {
            'status': 0,
            'cdrContent': mock_cdr,
            'faultcode': None,
            'faultstring': None
        }

    def send_pack(self, zip_content, file_name):
        import random
        import uuid
        import time

        time.sleep(random.uniform(1.0, 2.0))

        if random.random() < 0.9:
            return {
                'status': 0,
                'ticket': f"LOTE-{uuid.uuid4().hex[:10].upper()}",
                'faultcode': None,
                'faultstring': None
            }
        else:
            return {
                'status': 99,
                'ticket': None,
                'faultcode': '3000',
                'faultstring': random.choice([
                    "Error de lote: Archivos duplicados",
                    "Error de lote: Fecha de emisión不一致",
                    "Error de lote: Estructura ZIP inválida",
                ])
            }


def get_ose_client(use_mock=None):
    """Factory function para obtener el cliente OSE apropiado."""
    if use_mock is None:
        use_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)

    if use_mock:
        logger.info("Usando MockOSEClient (desarrollo local)")
        return MockOSEClient()
    else:
        wsdl = os.getenv('SUNAT_OSE_WSDL', '')
        logger.info("Usando OSEClient (conexión real)")
        return OSEClient() if wsdl else None