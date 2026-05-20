"""
Management command para verificar la configuracion de SUNAT/OSE.

Uso:
    python manage.py verificar_sunat
"""
import os
import base64
import zipfile
import logging
from io import BytesIO
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from lxml import etree

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verifica la configuracion de SUNAT/OSE (certificado, credenciales, conexion)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-firma',
            action='store_true',
            help='Prueba la firma digital con un XML de ejemplo',
        )
        parser.add_argument(
            '--test-conexion',
            action='store_true',
            help='Prueba la conexion con SUNAT/OSE (requiere SUNAT_OSE_MOCK=False)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('  VERIFICACION DE CONFIGURACION SUNAT/OSE'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')

        all_ok = True

        # 1. Verificar modo MOCK
        all_ok &= self._verificar_mock()

        # 2. Verificar certificado digital
        all_ok &= self._verificar_certificado()

        # 3. Verificar credenciales OSE
        all_ok &= self._verificar_credenciales()

        # 4. Verificar WSDL
        all_ok &= self._verificar_wsdl()

        # 5. Verificar estructura XML
        all_ok &= self._verificar_estructura_xml()

        # 6. Prueba de firma (opcional)
        if options.get('test_firma'):
            all_ok &= self._prueba_firma()

        # 7. Prueba de conexion (opcional)
        if options.get('test_conexion'):
            all_ok &= self._prueba_conexion()

        self.stdout.write('')
        if all_ok:
            self.stdout.write(self.style.SUCCESS('VERIFICACION COMPLETADA - Todo parece correcto'))
        else:
            self.stdout.write(self.style.WARNING(
                'VERIFICACION COMPLETADA - Hay problemas que requieren atencion'
            ))
            self.stdout.write(self.style.WARNING(
                'Para conexion real a SUNAT: SUNAT_OSE_MOCK=False en .env o docker-compose.yml'
            ))

    def _verificar_mock(self):
        self.stdout.write(self.style.HTTP_INFO('[1/5] Modo de operacion:'))
        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        
        if es_mock:
            self.stdout.write(self.style.WARNING(
                '  [!] MODO MOCK ACTIVADO - Las facturas NO se envian a SUNAT real'
            ))
            self.stdout.write(self.style.WARNING(
                '  [!] Para enviar a SUNAT: Cambiar SUNAT_OSE_MOCK=False'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  [OK] MODO REAL - Se conectara a SUNAT/OSE'))
        
        return True

    def _verificar_certificado(self):
        self.stdout.write(self.style.HTTP_INFO('[2/5] Certificado digital:'))
        
        cert_path = os.getenv('SUNAT_CERT_PATH', '')
        cert_password = os.getenv('SUNAT_CERT_PASSWORD', '')
        
        if not cert_path:
            self.stdout.write(self.style.ERROR('  [ERROR] SUNAT_CERT_PATH no configurado'))
            return False
        
        # Resolver path absoluto
        import pathlib
        resolved = pathlib.Path(cert_path)
        if not resolved.is_absolute():
            resolved = pathlib.Path(settings.BASE_DIR) / resolved
        
        if not resolved.exists():
            self.stdout.write(self.style.ERROR(f'  [ERROR] Certificado no encontrado: {resolved}'))
            return False
        
        self.stdout.write(self.style.SUCCESS(f'  [OK] Certificado encontrado: {resolved}'))
        
        # Verificar que se puede cargar
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            with open(resolved, 'rb') as f:
                cert_data = f.read()
            
            private_key, certificate, _ = pkcs12.load_key_and_certificates(
                cert_data,
                cert_password.encode('utf-8') if cert_password else None
            )
            
            # Mostrar info del certificado
            subject = certificate.subject
            issuer = certificate.issuer
            not_valid_before = certificate.not_valid_before_utc
            not_valid_after = certificate.not_valid_after_utc
            
            self.stdout.write(self.style.SUCCESS(f'  [OK] Certificado valido'))
            self.stdout.write(f'       Subject: {subject.rfc4514_string()}')
            self.stdout.write(f'       Vence: {not_valid_after}')
            
            import datetime
            if not_valid_after < datetime.datetime.now(datetime.timezone.utc):
                self.stdout.write(self.style.ERROR('  [ERROR] Certificado EXPIRADO'))
                return False
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] No se pudo cargar el certificado: {e}'))
            return False

    def _verificar_credenciales(self):
        self.stdout.write(self.style.HTTP_INFO('[3/5] Credenciales OSE:'))
        
        ruc = os.getenv('SUNAT_OSE_RUC', '')
        usuario = os.getenv('SUNAT_OSE_USUARIO', '')
        password = os.getenv('SUNAT_OSE_PASSWORD', '')
        
        if not ruc:
            self.stdout.write(self.style.ERROR('  [ERROR] SUNAT_OSE_RUC no configurado'))
            return False
        if len(ruc) != 11:
            self.stdout.write(self.style.ERROR(f'  [ERROR] RUC invalido ({len(ruc)} digitos, debe ser 11)'))
            return False
        
        self.stdout.write(self.style.SUCCESS(f'  [OK] RUC: {ruc}'))
        
        if not usuario:
            self.stdout.write(self.style.ERROR('  [ERROR] SUNAT_OSE_USUARIO no configurado'))
            return False
        self.stdout.write(self.style.SUCCESS(f'  [OK] Usuario: {ruc}-{usuario}'))
        
        if not password:
            self.stdout.write(self.style.ERROR('  [ERROR] SUNAT_OSE_PASSWORD no configurado'))
            return False
        self.stdout.write(self.style.SUCCESS(f'  [OK] Password: {"*" * len(password)}'))
        
        return True

    def _verificar_wsdl(self):
        self.stdout.write(self.style.HTTP_INFO('[4/5] WSDL:'))
        
        wsdl_url = os.getenv('SUNAT_OSE_WSDL', '')
        
        if not wsdl_url:
            self.stdout.write(self.style.WARNING('  [!] SUNAT_OSE_WSDL no configurado'))
            self.stdout.write(self.style.WARNING('      Se usara WSDL local si esta disponible'))
            return True
        
        self.stdout.write(self.style.SUCCESS(f'  [OK] WSDL URL: {wsdl_url}'))
        
        # Verificar WSDL local
        wsdl_local = os.path.join(str(settings.BASE_DIR), 'wsdl', 'billService.wsdl')
        if os.path.exists(wsdl_local):
            self.stdout.write(self.style.SUCCESS(f'  [OK] WSDL local encontrado: {wsdl_local}'))
        else:
            self.stdout.write(self.style.WARNING(f'  [!] WSDL local no encontrado: {wsdl_local}'))
        
        return True

    def _verificar_estructura_xml(self):
        self.stdout.write(self.style.HTTP_INFO('[5/5] Estructura XML UBL:'))
        
        # Verificar que se puede generar un XML basico
        try:
            from apps.sunat_ose.xml_generator import generar_xml_ubl
            from apps.comprobantes.models import Comprobante
            
            comprobante = Comprobante.objects.first()
            if not comprobante:
                self.stdout.write(self.style.WARNING('  [!] No hay comprobantes en la BD para probar'))
                return True
            
            xml_content = generar_xml_ubl(comprobante)
            root = etree.fromstring(xml_content)
            
            # Verificar estructura basica
            ns = {'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'}
            ubl_version = root.find('.//cbc:UBLVersionID', ns)
            if ubl_version is not None and ubl_version.text == '2.1':
                self.stdout.write(self.style.SUCCESS('  [OK] UBL Version: 2.1'))
            else:
                self.stdout.write(self.style.ERROR('  [ERROR] UBL Version incorrecta'))
                return False
            
            # Verificar que tiene UBLExtensions (donde va la firma)
            ns_ext = {'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2'}
            ubl_ext = root.find('.//ext:UBLExtensions', ns_ext)
            if ubl_ext is not None:
                self.stdout.write(self.style.SUCCESS('  [OK] UBLExtensions presente'))
            else:
                self.stdout.write(self.style.ERROR('  [ERROR] UBLExtensions no encontrado'))
                return False
            
            self.stdout.write(self.style.SUCCESS('  [OK] Estructura XML UBL correcta'))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Error verificando estructura XML: {e}'))
            return False

    def _prueba_firma(self):
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('[PRUEBA] Firma digital:'))
        
        try:
            from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml
            from apps.comprobantes.models import Comprobante
            
            comprobante = Comprobante.objects.first()
            if not comprobante:
                self.stdout.write(self.style.WARNING('  [!] No hay comprobantes para probar firma'))
                return True
            
            xml_content = generar_xml_ubl(comprobante)
            xml_firmado = firmar_xml(xml_content, empresa_id=comprobante.empresa_id)
            
            # Verificar que contiene firma
            if b'<ds:Signature' in xml_firmado or b'<Signature' in xml_firmado:
                self.stdout.write(self.style.SUCCESS('  [OK] XML firmado correctamente'))
            else:
                self.stdout.write(self.style.ERROR('  [ERROR] XML NO contiene firma digital'))
                return False
            
            if b'<X509Certificate>' in xml_firmado:
                self.stdout.write(self.style.SUCCESS('  [OK] Certificado X509 incluido en la firma'))
            else:
                self.stdout.write(self.style.ERROR('  [ERROR] Certificado X509 no encontrado'))
                return False
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Error en prueba de firma: {e}'))
            return False

    def _prueba_conexion(self):
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('[PRUEBA] Conexion con SUNAT/OSE:'))
        
        es_mock = getattr(settings, 'SUNAT_OSE_MOCK', True)
        if es_mock:
            self.stdout.write(self.style.WARNING(
                '  [!] No se puede probar conexion real con SUNAT_OSE_MOCK=True'
            ))
            self.stdout.write(self.style.WARNING(
                '      Cambie a SUNAT_OSE_MOCK=False y vuelva a intentar'
            ))
            return True
        
        try:
            from apps.sunat_ose.ose_client import get_ose_client
            
            client = get_ose_client(use_mock=False)
            if client is None:
                self.stdout.write(self.style.ERROR('  [ERROR] No se pudo crear el cliente OSE'))
                return False
            
            self.stdout.write(self.style.SUCCESS('  [OK] Cliente OSE creado exitosamente'))
            self.stdout.write(self.style.SUCCESS('  [OK] WSDL cargado correctamente'))
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [ERROR] Error de conexion: {e}'))
            return False
