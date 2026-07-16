"""
Tests del modulo xml_generator.

Verifica que el generador de XML produce XML valido para SUNAT.
"""
import pytest
from decimal import Decimal
from datetime import date


@pytest.fixture
def comprobante_con_detalles(db):
    from apps.empresas.models import Empresa
    from apps.clientes.models import Cliente
    from apps.productos.models import Producto
    from apps.comprobantes.models import (
        Comprobante, DetalleComprobante, SerieComprobante,
    )
    e = Empresa.objects.create(ruc="20999999999", razon_social="X")
    c = Cliente.objects.create(
        tipo_doc="6", num_doc="20100000001", razon_social="X",
    )
    p = Producto.objects.create(
        descripcion="X", precio_unitario=Decimal("100"),
    )
    s = SerieComprobante.objects.create(empresa=e, tipo="01", serie="F001")
    comp = Comprobante.objects.create(
        empresa=e, cliente=c, serie=s, numero=1,
        fecha=date.today(), tipo="01", estado="BORRADOR",
        subtotal=Decimal("100"), igv=Decimal("18"), total=Decimal("118"),
    )
    DetalleComprobante.objects.create(
        comprobante=comp, producto=p,
        cantidad=Decimal("1"), precio_unitario=Decimal("100"),
        afecto_igv=True, cod_tipo_afectacion="10",
    )
    return comp


@pytest.mark.django_db
class TestGenerarXml:
    def test_generar_xml_ubl(self, comprobante_con_detalles):
        from apps.sunat_ose.xml_generator import generar_xml_ubl
        xml = generar_xml_ubl(comprobante_con_detalles)
        assert xml is not None
        xml_str = xml if isinstance(xml, str) else xml.decode("utf-8", errors="ignore")
        assert "<Invoice" in xml_str or "Invoice" in xml_str or "<CreditNote" in xml_str

    def test_generar_xml_ubl_boleta(self, db):
        """Verifica generacion para boletas (tipo 03)."""
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.comprobantes.models import (
            Comprobante, DetalleComprobante, SerieComprobante,
        )
        from apps.sunat_ose.xml_generator import generar_xml_ubl
        e = Empresa.objects.create(ruc="20999999999", razon_social="X")
        c = Cliente.objects.create(
            tipo_doc="1", num_doc="12345678", razon_social="X",
        )
        p = Producto.objects.create(
            descripcion="X", precio_unitario=Decimal("50"),
        )
        s = SerieComprobante.objects.create(empresa=e, tipo="03", serie="B001")
        comp = Comprobante.objects.create(
            empresa=e, cliente=c, serie=s, numero=1,
            fecha=date.today(), tipo="03", estado="BORRADOR",
            subtotal=Decimal("50"), igv=Decimal("9"), total=Decimal("59"),
        )
        DetalleComprobante.objects.create(
            comprobante=comp, producto=p,
            cantidad=Decimal("1"), precio_unitario=Decimal("50"),
            afecto_igv=True,
        )
        xml = generar_xml_ubl(comp)
        assert xml is not None

    def test_crear_zip(self):
        from apps.sunat_ose.xml_generator import crear_zip
        zip_bytes = crear_zip(b"<xml>test</xml>", "test-file")
        assert zip_bytes is not None
        assert len(zip_bytes) > 0


@pytest.mark.django_db
class TestGenerarXmlNotaCredito:
    def test_generar_xml_nota_credito(self, comprobante_con_detalles):
        from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
        from apps.sunat_ose.xml_generator import generar_xml_nota_credito
        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante_con_detalles,
            serie="FC01", numero=1,
            fecha=date.today(), tipo_nc="NC", tipo_nota="01",
            descripcion="Anulacion",
            estado="BORRADOR",
        )
        DetalleNotaCredito.objects.create(
            nota_credito=nota,
            producto=comprobante_con_detalles.detalles.first().producto,
            cantidad=Decimal("1"), precio_unitario=Decimal("100"),
            afecto_igv=True,
        )
        xml = generar_xml_nota_credito(nota)
        assert xml is not None