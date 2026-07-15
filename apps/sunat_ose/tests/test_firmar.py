"""
Tests del firmador XML.

Verifica que la firma digital funciona correctamente.
"""
import pytest


class TestFirmarXml:
    """Tests de apps.sunat_ose.firmar."""

    def test_get_cert_from_db_empresa_inexistente(self):
        """Si la empresa no existe, debe lanzar excepcion."""
        from apps.sunat_ose.firmar import get_cert_from_db
        with pytest.raises(Exception):
            get_cert_from_db(empresa_id=99999)

    def test_sign_xml_sin_certificado(self):
        """Si no hay certificado, debe lanzar excepcion."""
        from apps.sunat_ose.firmar import sign_xml
        with pytest.raises(Exception):
            sign_xml("<xml>test</xml>", cert_path="", cert_password="")

    def test_get_cert_bytes_archivo_inexistente(self):
        """Si el archivo no existe, debe lanzar excepcion."""
        from apps.sunat_ose.firmar import get_cert_bytes
        with pytest.raises(Exception):
            get_cert_bytes("/path/inexistente/cert.pfx")


class TestValidarXmlFirmado:
    """Tests de la validacion de XML firmado."""

    def test_validar_xml_sin_firma(self):
        from apps.sunat_ose.services import _validar_xml_firmado
        from dominio.excepciones import FirmaDigitalInvalida
        with pytest.raises(FirmaDigitalInvalida):
            _validar_xml_firmado(b"<xml>no firmado</xml>")

    def test_validar_xml_con_firma_sin_cert(self):
        from apps.sunat_ose.services import _validar_xml_firmado
        from dominio.excepciones import FirmaDigitalInvalida
        xml = b"<xml><ds:Signature>signed</ds:Signature></xml>"
        with pytest.raises(FirmaDigitalInvalida):
            _validar_xml_firmado(xml)

    def test_validar_xml_con_firma_y_cert_ok(self):
        from apps.sunat_ose.services import _validar_xml_firmado
        xml = b"<xml><ds:Signature><ds:X509Certificate>cert</ds:X509Certificate></ds:Signature></xml>"
        # No debe lanzar excepcion
        _validar_xml_firmado(xml)

    def test_validar_xml_string(self):
        from apps.sunat_ose.services import _validar_xml_firmado
        xml_str = "<xml><ds:Signature><ds:X509Certificate>cert</ds:X509Certificate></ds:Signature></xml>"
        _validar_xml_firmado(xml_str)