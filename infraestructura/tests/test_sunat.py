"""
Tests del adaptador Mock del OSE.
"""
import pytest
import base64

from infraestructura.sunat.mock_ose import MockOSEAdapter


class TestMockOSEAdapter:
    def test_send_bill_exitoso(self):
        ose = MockOSEAdapter()
        result = ose.send_bill(b"contenido zip", "test.zip")
        assert result["status"] == 0
        assert result.get("ticket") is not None
        assert result.get("applicationResponse") is not None

    def test_send_bill_rechazado_con_tasa(self):
        ose = MockOSEAdapter(tasa_rechazo=1.0)  # siempre rechaza
        result = ose.send_bill(b"contenido zip", "test.zip")
        assert result["status"] != 0
        assert "faultstring" in result

    def test_get_status_con_ticket_conocido(self):
        ose = MockOSEAdapter()
        bill_result = ose.send_bill(b"zip", "test.zip")
        ticket = bill_result["ticket"]
        status_result = ose.get_status(ticket)
        assert status_result["status"] == 0

    def test_get_status_con_ticket_desconocido(self):
        ose = MockOSEAdapter()
        status_result = ose.get_status("ticket-inexistente")
        assert status_result["status"] == 0  # desconocido = ok por defecto

    def test_get_status_cdr(self):
        ose = MockOSEAdapter()
        bill_result = ose.send_bill(b"zip", "test.zip")
        ticket = bill_result["ticket"]
        cdr = ose.get_status_cdr(ticket)
        assert "cdrContent" in cdr


class TestZipHelper:
    def test_crear_zip(self):
        from infraestructura.sunat.zip_helper import crear_zip
        xml = b"<xml>test</xml>"
        zip_bytes = crear_zip(xml, "test-file")
        assert zip_bytes is not None
        assert len(zip_bytes) > 0
        import zipfile
        from io import BytesIO
        zf = zipfile.ZipFile(BytesIO(zip_bytes), "r")
        names = zf.namelist()
        assert "test-file.xml" in names

    def test_crear_zip_con_string(self):
        from infraestructura.sunat.zip_helper import crear_zip
        xml = "<xml>test</xml>"  # string, no bytes
        zip_bytes = crear_zip(xml, "test-file")
        assert zip_bytes is not None


class TestXmlGeneratorAdapter:
    @pytest.mark.django_db
    def test_generar_con_comprobante_django(self):
        from decimal import Decimal
        from datetime import date
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.comprobantes.models import (
            Comprobante as CompModel,
            DetalleComprobante,
            SerieComprobante,
        )
        from apps.productos.models import Producto
        from infraestructura.sunat.xml_generator_adapter import XmlGeneratorAdapter

        e = Empresa.objects.create(ruc="20999999999", razon_social="Test SA")
        c = Cliente.objects.create(
            tipo_doc="6", num_doc="20100000001", razon_social="Cliente SA",
        )
        p = Producto.objects.create(
            descripcion="Test", precio_unitario=Decimal("100"),
        )
        s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
        comp = CompModel.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="01", estado="BORRADOR",
            subtotal=Decimal("100"), igv=Decimal("18"), total=Decimal("118"),
        )
        DetalleComprobante.objects.create(
            comprobante=comp, producto=p,
            cantidad=Decimal("1"), precio_unitario=Decimal("100"),
            afecto_igv=True,
        )
        adapter = XmlGeneratorAdapter()
        xml = adapter.generar(comp)
        assert xml is not None
        xml_str = xml if isinstance(xml, str) else xml.decode("utf-8", errors="ignore")
        assert ("<?xml" in xml_str or "<Invoice" in xml_str
                or "<CreditNote" in xml_str or "<DespatchAdvice" in xml_str)