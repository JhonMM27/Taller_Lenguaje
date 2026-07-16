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
    def test_catalogo_05_contiene_todos_los_tributos_documentados(self):
        from dominio.tributos import TRIBUTOS_SUNAT

        assert set(TRIBUTOS_SUNAT) == {
            "1000", "1016", "2000", "3000", "7152",
            "9995", "9996", "9997", "9998", "9999",
        }

    @pytest.mark.parametrize("codigo,tributo,nombre,tipo,tasa,categoria", [
        ("10", "1000", "IGV", "VAT", "18.00", "S"),
        ("11", "9996", "GRA", "FRE", "18.00", "Z"),
        ("12", "9996", "GRA", "FRE", "18.00", "Z"),
        ("13", "9996", "GRA", "FRE", "18.00", "Z"),
        ("14", "9996", "GRA", "FRE", "18.00", "Z"),
        ("15", "9996", "GRA", "FRE", "18.00", "Z"),
        ("16", "9996", "GRA", "FRE", "18.00", "Z"),
        ("17", "1016", "IVAP", "VAT", "4.00", "S"),
        ("20", "9997", "EXO", "VAT", "0.00", "E"),
        ("21", "9996", "GRA", "FRE", "0.00", "Z"),
        ("30", "9998", "INA", "FRE", "0.00", "O"),
        ("31", "9996", "GRA", "FRE", "0.00", "Z"),
        ("32", "9996", "GRA", "FRE", "0.00", "Z"),
        ("33", "9996", "GRA", "FRE", "0.00", "Z"),
        ("34", "9996", "GRA", "FRE", "0.00", "Z"),
        ("35", "9996", "GRA", "FRE", "0.00", "Z"),
        ("36", "9996", "GRA", "FRE", "0.00", "Z"),
        ("37", "9996", "GRA", "FRE", "0.00", "Z"),
        ("40", "9995", "EXP", "FRE", "0.00", "G"),
    ])
    def test_catalogos_afectacion_y_tributo(
        self, codigo, tributo, nombre, tipo, tasa, categoria,
    ):
        from apps.sunat_ose.xml_generator import obtener_datos_igv

        datos = obtener_datos_igv(codigo)
        assert datos["tributo_id"] == tributo
        assert datos["tributo_nombre"] == nombre
        assert datos["tributo_tipo"] == tipo
        assert datos["tasa"] == tasa
        assert datos["categoria"] == categoria

    def test_generar_xml_ubl(self, comprobante_con_detalles):
        from apps.sunat_ose.xml_generator import generar_xml_ubl
        xml = generar_xml_ubl(comprobante_con_detalles)
        assert xml is not None
        xml_str = xml if isinstance(xml, str) else xml.decode("utf-8", errors="ignore")
        assert "<Invoice" in xml_str or "Invoice" in xml_str or "<CreditNote" in xml_str

    def test_factura_con_dni_falla_antes_del_envio(self, comprobante_con_detalles):
        from dominio.excepciones import TipoDocumentoInvalido
        from apps.sunat_ose.xml_generator import generar_xml_ubl

        cliente = comprobante_con_detalles.cliente
        cliente.tipo_doc = "1"
        cliente.num_doc = "74408272"
        cliente.save()
        comprobante_con_detalles.refresh_from_db()

        with pytest.raises(TipoDocumentoInvalido, match="RUC"):
            generar_xml_ubl(comprobante_con_detalles)

    def test_operacion_gratuita_usa_valor_referencial(self, comprobante_con_detalles):
        from lxml import etree
        from apps.sunat_ose.xml_generator import generar_xml_ubl

        detalle = comprobante_con_detalles.detalles.first()
        detalle.producto.cod_tipo_afectacion = "35"
        detalle.producto.save()
        detalle.cod_tipo_afectacion = "35"
        detalle.afecto_igv = False
        detalle.subtotal = Decimal("0")
        detalle.igv_linea = Decimal("0")
        detalle.save()
        comprobante_con_detalles.subtotal = Decimal("0")
        comprobante_con_detalles.igv = Decimal("0")
        comprobante_con_detalles.total = Decimal("0")
        comprobante_con_detalles.save()

        root = etree.fromstring(generar_xml_ubl(comprobante_con_detalles))
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        linea = root.xpath("//cac:InvoiceLine", namespaces=ns)[0]
        assert linea.xpath("string(./cbc:LineExtensionAmount)", namespaces=ns) == "100.00"
        assert linea.xpath(
            "string(./cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount)", namespaces=ns
        ) == "100.00"
        assert linea.xpath(
            "string(./cac:TaxTotal/cbc:TaxAmount)", namespaces=ns
        ) == "0.00"
        assert linea.xpath("string(./cac:Price/cbc:PriceAmount)", namespaces=ns) == "0.00"
        assert linea.xpath(
            "string(./cac:PricingReference/cac:AlternativeConditionPrice/cbc:PriceTypeCode)",
            namespaces=ns,
        ) == "02"
        assert linea.xpath(
            "string(./cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID)",
            namespaces=ns,
        ) == "9996"
        assert root.xpath("string(//cbc:Note/@languageLocaleID)", namespaces=ns) == "1002"
        assert root.xpath(
            "string(//*[local-name()='AdditionalMonetaryTotal'][cbc:ID='1004']/cbc:PayableAmount)",
            namespaces=ns,
        ) == "100.00"

    def test_gratuito_gravado_informa_igv_referencial_sin_cobrarlo(
        self, comprobante_con_detalles,
    ):
        from lxml import etree
        from apps.sunat_ose.xml_generator import generar_xml_ubl

        detalle = comprobante_con_detalles.detalles.first()
        detalle.cod_tipo_afectacion = "11"
        detalle.subtotal = Decimal("0")
        detalle.igv_linea = Decimal("0")
        detalle.afecto_igv = False
        detalle.save()
        comprobante_con_detalles.subtotal = Decimal("0")
        comprobante_con_detalles.igv = Decimal("0")
        comprobante_con_detalles.total = Decimal("0")
        comprobante_con_detalles.save()

        root = etree.fromstring(generar_xml_ubl(comprobante_con_detalles))
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        linea = root.xpath("//cac:InvoiceLine", namespaces=ns)[0]
        assert linea.xpath("string(./cbc:LineExtensionAmount)", namespaces=ns) == "100.00"
        assert linea.xpath("string(./cac:TaxTotal/cbc:TaxAmount)", namespaces=ns) == "0.00"
        assert linea.xpath(
            "string(./cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount)", namespaces=ns
        ) == "18.00"
        assert root.xpath(
            "string(//cac:LegalMonetaryTotal/cbc:PayableAmount)", namespaces=ns
        ) == "0.00"

    def test_exportacion_0200_con_receptor_no_domiciliado(self, db):
        from lxml import etree
        from apps.empresas.models import Empresa
        from apps.clientes.models import Cliente
        from apps.productos.models import Producto
        from apps.comprobantes.models import Comprobante, DetalleComprobante, SerieComprobante
        from apps.sunat_ose.xml_generator import generar_xml_ubl

        empresa = Empresa.objects.create(ruc="20999999998", razon_social="Exportador")
        cliente = Cliente.objects.create(
            tipo_doc="0", num_doc="FOREIGN-001", razon_social="Foreign Buyer",
            pais_codigo="US",
        )
        producto = Producto.objects.create(
            codigo="EXP-1", descripcion="Bien exportado",
            precio_unitario=Decimal("100"), cod_tipo_afectacion="40",
        )
        serie = SerieComprobante.objects.create(empresa=empresa, tipo="01", serie="F001")
        comp = Comprobante.objects.create(
            empresa=empresa, cliente=cliente, serie=serie, numero=1,
            fecha=date.today(), tipo="01", tipo_operacion="0200", moneda="USD",
            subtotal=Decimal("100"), igv=Decimal("0"), total=Decimal("100"),
        )
        DetalleComprobante.objects.create(
            comprobante=comp, producto=producto, cantidad=Decimal("1"),
            precio_unitario=Decimal("100"), subtotal=Decimal("100"),
            cod_tipo_afectacion="40", afecto_igv=False,
        )

        root = etree.fromstring(generar_xml_ubl(comp))
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        assert root.xpath("string(./cbc:ProfileID)", namespaces=ns) == "0200"
        assert root.xpath("string(./cbc:InvoiceTypeCode/@listID)", namespaces=ns) == "0200"
        assert root.xpath("string(./cbc:DocumentCurrencyCode)", namespaces=ns) == "USD"
        assert root.xpath(
            "string(//cac:AccountingCustomerParty//cbc:ID/@schemeID)", namespaces=ns
        ) == "0"
        assert root.xpath(
            "string(//cac:InvoiceLine//cac:TaxScheme/cbc:ID)", namespaces=ns
        ) == "9995"

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

    def test_precios_de_linea_usan_importe_modificado(self, comprobante_con_detalles):
        """Regresion SUNAT 3271: cantidad * valor unitario debe igualar la linea."""
        from lxml import etree
        from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
        from apps.sunat_ose.xml_generator import generar_xml_nota_credito

        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante_con_detalles,
            serie="FC01", numero=2,
            fecha=date.today(), tipo_nc="NCD", tipo_nota="05",
            descripcion="Descuento por item", estado="RECHAZADO",
            op_gravada=Decimal("50.00"), igv=Decimal("9.00"),
            importe=Decimal("59.00"),
        )
        DetalleNotaCredito.objects.create(
            nota_credito=nota,
            producto=comprobante_con_detalles.detalles.first().producto,
            cantidad=Decimal("1"), precio_unitario=Decimal("100"),
            descuento=Decimal("50"), subtotal=Decimal("50"),
            igv_linea=Decimal("9"), afecto_igv=True,
            cod_tipo_afectacion="10",
        )

        root = etree.fromstring(generar_xml_nota_credito(nota))
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        linea = root.xpath("//cac:CreditNoteLine", namespaces=ns)[0]

        assert linea.xpath("string(./cbc:LineExtensionAmount)", namespaces=ns) == "50.00"
        assert linea.xpath("string(./cac:Price/cbc:PriceAmount)", namespaces=ns) == "50.0000000000"
        assert linea.xpath(
            "string(./cac:PricingReference/cac:AlternativeConditionPrice/cbc:PriceAmount)",
            namespaces=ns,
        ) == "59.0000000000"

    def test_nota_credito_gratuita_mantiene_base_referencial(
        self, comprobante_con_detalles,
    ):
        from lxml import etree
        from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
        from apps.sunat_ose.xml_generator import generar_xml_nota_credito

        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante_con_detalles,
            serie="FC01", numero=3, fecha=date.today(), tipo_nota="08",
            op_gravada=Decimal("0"), igv=Decimal("0"), importe=Decimal("0"),
        )
        DetalleNotaCredito.objects.create(
            nota_credito=nota,
            producto=comprobante_con_detalles.detalles.first().producto,
            cantidad=Decimal("1"), precio_unitario=Decimal("100"),
            subtotal=Decimal("0"), igv_linea=Decimal("0"),
            cod_tipo_afectacion="37", afecto_igv=False,
        )
        root = etree.fromstring(generar_xml_nota_credito(nota))
        ns = {
            "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
        }
        linea = root.xpath("//cac:CreditNoteLine", namespaces=ns)[0]
        assert linea.xpath("string(./cbc:LineExtensionAmount)", namespaces=ns) == "100.00"
        assert linea.xpath(
            "string(./cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount)", namespaces=ns
        ) == "100.00"
        assert linea.xpath("string(./cac:Price/cbc:PriceAmount)", namespaces=ns) == "0.00"
