"""
SUNAT OSE Client - Para entorno BETA/DESARROLLO
Manual Técnico de Operatividad OSE v5.2

Este cliente implementa los métodos SOAP del Manual SUNAT:
- sendBill: Envío de comprobantes individuales (facturas, boletas, notas)
- getStatus: Consulta de estado por ticket
- getStatusCdr: Consulta de CDR por ticket

Para producción, reemplazar con credenciales y endpoints reales del OSE certificador.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class OSEClient:
    """
    Cliente SOAP para comunicación con OSE (Operador de Servicios Electrónicos)
    
    Según Manual SUNAT, el OSE debe exponer:
    - https://xxx/ol-ti-itcpe/billService (para sendBill y getStatus)
    """
    
    def __init__(self, wsdl_url=None, ruc=None, usuario=None, password=None):
        self.wsdl_url = wsdl_url or getattr(settings, 'SUNAT_OSE_WSDL', '')
        self.ruc = ruc or getattr(settings, 'SUNAT_OSE_RUC', '')
        self.usuario = usuario or getattr(settings, 'SUNAT_OSE_USUARIO', '')
        self.password = password or getattr(settings, 'SUNAT_OSE_PASSWORD', '')
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                import zeep
                from zeep.exceptions import TransportError
                self._client = zeep.Client(self.wsdl_url)
                logger.info(f"Conectado al OSE: {self.wsdl_url}")
            except TransportError as e:
                logger.error(f"Error conectando al OSE: {e}")
                raise ConnectionError(f"No se pudo conectar al OSE: {e}")
        return self._client
    
    def send_bill(self, zip_content, file_name):
        """
        Envía comprobante de pago electrónico al OSE.
        
        Args:
            zip_content: Contenido del ZIP (bytes)
            file_name: Nombre del archivo (ej: 20123456789-01-F001-00000001.zip)
        
        Returns:
            dict: Respuesta del OSE con ticket para consulta
        
        Según Manual SUNAT:
        - Atributos de entrada: zipContent (base64), fileName (string)
        - Atributos de salida: status (int), ticket (string), faultcode (string)
        """
        from zeep.exceptions import Fault
        try:
            logger.info(f"Enviando comprobante: {file_name}")
            
            response = self.client.service.sendBill(
                zipContent=zip_content,
                fileName=file_name
            )
            
            logger.info(f"Respuesta OSE - status: {response.status}, ticket: {response.ticket}")
            
            return {
                'status': response.status,
                'ticket': response.ticket,
                'faultcode': getattr(response, 'faultcode', None),
                'faultstring': getattr(response, 'faultstring', None)
            }
            
        except Fault as e:
            logger.error(f"Fault del OSE: {e.message}")
            return {
                'status': -1,
                'faultcode': e.message.get('faultcode', 'UNKNOWN'),
                'faultstring': str(e)
            }
        except Exception as e:
            logger.error(f"Error enviando a OSE: {str(e)}")
            raise
    
    def get_status(self, ticket):
        """
        Consulta el estado de un comprobante enviado usando el ticket.
        
        Args:
            ticket: Ticket recibido de sendBill
        
        Returns:
            dict: Estado del comprobante
        
        Códigos de respuesta según Manual SUNAT:
        - 0: Aceptado
        - 99: En proceso
        - 99: Rechazado (detalle en faultstring)
        """
        from zeep.exceptions import Fault
        try:
            logger.info(f"Consultando ticket: {ticket}")
            
            response = self.client.service.getStatus(
                ticket=ticket
            )
            
            logger.info(f"Estado ticket {ticket}: {response.status}")
            
            return {
                'status': response.status,
                'ticket': ticket,
                'faultcode': getattr(response, 'faultcode', None),
                'faultstring': getattr(response, 'faultstring', None)
            }
            
        except Fault as e:
            logger.error(f"Fault consultando ticket: {e.message}")
            return {
                'status': -1,
                'faultcode': e.message.get('faultcode', 'UNKNOWN'),
                'faultstring': str(e)
            }
        except Exception as e:
            logger.error(f"Error consultando ticket: {str(e)}")
            raise
    
    def get_status_cdr(self, ticket):
        """
        Consulta y obtiene el CDR (Constancia de Recepción) del OSE.
        
        Args:
            ticket: Ticket del comprobante
        
        Returns:
            dict: CDR en base64
        """
        from zeep.exceptions import Fault
        try:
            logger.info(f"Consultando CDR para ticket: {ticket}")
            
            response = self.client.service.getStatusCdr(
                ticket=ticket
            )
            
            return {
                'status': response.status,
                'cdrContent': getattr(response, 'cdrContent', None),
                'faultcode': getattr(response, 'faultcode', None),
                'faultstring': getattr(response, 'faultstring', None)
            }
            
        except Fault as e:
            logger.error(f"Fault consultando CDR: {e.message}")
            return {
                'status': -1,
                'faultcode': e.message.get('faultcode', 'UNKNOWN'),
                'faultstring': str(e)
            }
        except Exception as e:
            logger.error(f"Error consultando CDR: {str(e)}")
            raise

    def send_pack(self, zip_content, file_name):
        """
        Envía lote de comprobantes al OSE (SendPack).
        
        Args:
            zip_content: Contenido del ZIP con múltiples XML (base64)
            file_name: Nombre del archivo (ej: 20123456789-LT-20260425-1.zip)
        
        Returns:
            dict: Respuesta del OSE con ticket para consulta
        
        Según Manual SUNAT, SendPack permite hasta 1000 archivos por lote.
        """
        from zeep.exceptions import Fault
        try:
            logger.info(f"Enviando lote: {file_name}")
            
            response = self.client.service.sendPack(
                zipContent=zip_content,
                fileName=file_name
            )
            
            logger.info(f"Respuesta SendPack - status: {response.status}, ticket: {response.ticket}")
            
            return {
                'status': response.status,
                'ticket': response.ticket,
                'faultcode': getattr(response, 'faultcode', None),
                'faultstring': getattr(response, 'faultstring', None)
            }
            
        except Fault as e:
            logger.error(f"Fault del OSE: {e.message}")
            return {
                'status': -1,
                'faultcode': e.message.get('faultcode', 'UNKNOWN'),
                'faultstring': str(e)
            }
        except Exception as e:
            logger.error(f"Error enviando lote a OSE: {str(e)}")
            raise


class MockOSEClient:
    """
    Cliente MOCK para desarrollo local (NO conecta a SUNAT real)
    Simula respuestas del OSE según Manual SUNAT.
    """
    
    def __init__(self, *args, **kwargs):
        pass
    
    def send_bill(self, zip_content, file_name):
        """Simula envío - 90% aceptación, 10% rechazo"""
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
        """Simula consulta de estado"""
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
        """Simula consulta de CDR"""
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
        """Simula envío de lote - 90% aceptación, 10% rechazo"""
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
    """
    Factory function para obtener el cliente OSE apropiado.
    
    Args:
        use_mock: Forzar uso de mock (True/False/None para auto)
    
    Returns:
        OSEClient o MockOSEClient
    """
    if use_mock is None:
        use_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
    
    if use_mock:
        logger.info("Usando MockOSEClient (desarrollo local)")
        return MockOSEClient()
    else:
        logger.info("Usando OSEClient (conexión real)")
        return OSEClient() if settings.SUNAT_OSE_WSDL else None