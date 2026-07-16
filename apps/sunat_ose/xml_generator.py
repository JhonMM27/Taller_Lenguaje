import logging
from collections import defaultdict
from decimal import Decimal
from lxml import etree
from django.conf import settings
from dominio.excepciones import TipoDocumentoInvalido
from dominio.tributos import datos_afectacion_igv
from dominio.tributos import tipo_operacion_comprobante, validar_moneda

logger = logging.getLogger(__name__)


def _money(value):
    """Formatea importes UBL con los dos decimales exigidos por SUNAT."""
    return f"{Decimal(str(value or 0)).quantize(Decimal('0.01')):.2f}"

NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'inv': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
    'sac': 'urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1',
    'cn': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
}

TIPO_DOC_MAP = {
    '0': '0',
    '1': '1',
    '6': '6',
    '4': '4',
    '7': '7',
    'A': 'A',
}

TIPO_AFECTACION_MAP = {
    '10': 'VAT',
    '11': 'VAT',
    '12': 'VAT',
    '14': 'VAT',
    '15': 'VAT',
    '16': 'VAT',
    '17': 'ZER',
    '18': 'EXC',
    '20': 'VAT',
    '21': 'VAT',
    '30': 'FRE',
    '31': 'FRE',
    '32': 'FRE',
    '33': 'VAT',
    '34': 'VAT',
    '35': 'VAT',
    '36': 'VAT',
    '40': 'EXP',
    '41': 'EXP',
    '42': 'EXP',
    '50': 'OTH',
    '60': 'OTH',
    '80': 'OTH',
    '90': 'OTH',
}

UNIDADES_MEDIDA = {
    'NIU': 'NIU',
    'KG': 'KGM',
    'KGM': 'KGM',
    'GR': 'GRM',
    'GRM': 'GRM',
    'LT': 'LTR',
    'LTR': 'LTR',
    'ML': 'MLT',
    'MLT': 'MLT',
    'M': 'MTR',
    'MTR': 'MTR',
    'M2': 'MTK',
    'M3': 'MTC',
    'UM': 'NIU',
    'Caja': 'CJA',
    'CJA': 'CJA',
    'BX': 'BX',
    'Paquete': 'PAQ',
    'PAQ': 'PAQ',
    'UND': 'NIU',
    'UNI': 'NIU',
    'ZZ': 'ZZ',
    'H87': 'H87',
}


def obtener_datos_igv(cod_afectacion):
    """Traduce los catalogos SUNAT 07 y 05 a valores XML UBL."""
    datos = datos_afectacion_igv(str(cod_afectacion))
    tasa = datos['tasa']
    return {
        'tasa': f'{tasa:.2f}',
        'categoria': datos['categoria'],
        'tributo_id': datos['tributo_id'],
        'tributo_nombre': datos['nombre'],
        'tributo_tipo': datos['tipo'],
        'porcentaje_multiplicador': Decimal('1') + tasa / Decimal('100'),
        'gratuito': datos['gratuito'],
    }


def _validar_receptor(comprobante):
    """Evita enviar combinaciones que SUNAT rechazara con el codigo 2800."""
    tipo = comprobante.tipo or (comprobante.serie.tipo if comprobante.serie else '')
    cliente = comprobante.cliente
    try:
        tipo_derivado = tipo_operacion_comprobante(
            (det.cod_tipo_afectacion or det.producto.cod_tipo_afectacion)
            for det in comprobante.detalles.all()
        )
    except ValueError as exc:
        raise TipoDocumentoInvalido(str(exc)) from exc
    tipo_operacion = getattr(comprobante, 'tipo_operacion', None) or tipo_derivado
    if tipo_operacion != tipo_derivado:
        raise TipoDocumentoInvalido(
            "El tipo de operacion del comprobante no coincide con la afectacion de sus lineas."
        )
    if tipo_operacion == '0200':
        if tipo != '01' or cliente.tipo_doc not in ('0', '4', '7', 'A'):
            raise TipoDocumentoInvalido(
                "La exportacion 0200 requiere factura y receptor no domiciliado."
            )
        if str(getattr(cliente, 'pais_codigo', 'PE') or 'PE').upper() == 'PE':
            raise TipoDocumentoInvalido(
                "El receptor de una exportacion debe residir fuera de Peru."
            )
    elif tipo == '01' and cliente.tipo_doc != '6':
        raise TipoDocumentoInvalido(
            "SUNAT exige que el receptor de una factura tenga RUC (tipo 6). "
            "Para un cliente con DNI emita una boleta (tipo 03)."
        )
    from dominio.entidades.cliente import LONGITUDES_DOC, TIPOS_DOC_VALIDOS
    if cliente.tipo_doc not in TIPOS_DOC_VALIDOS:
        raise TipoDocumentoInvalido(
            f"Tipo de documento del receptor no permitido: {cliente.tipo_doc}."
        )
    esperado = LONGITUDES_DOC.get(cliente.tipo_doc)
    numero = str(cliente.num_doc or '').strip()
    if esperado and (not numero.isdigit() or len(numero) != esperado):
        raise TipoDocumentoInvalido(
            f"Documento del receptor invalido: el tipo {cliente.tipo_doc} "
            f"requiere {esperado} digitos."
        )
    if cliente.tipo_doc in ('0', '4', '7', 'A') and (
        not numero or len(numero) > 15 or any(c.isspace() for c in numero)
    ):
        raise TipoDocumentoInvalido(
            "El documento extranjero debe tener hasta 15 caracteres sin espacios."
        )
    return tipo_operacion


def _importes_tributarios_linea(detalle, es_nota_credito=False):
    """Calcula importes XML, incluyendo el tratamiento de operaciones gratuitas."""
    cod = getattr(detalle, 'cod_tipo_afectacion', None)
    if not cod and getattr(detalle, 'producto', None) is not None:
        cod = detalle.producto.cod_tipo_afectacion
    cod = cod or '10'
    datos = obtener_datos_igv(cod)
    cantidad = Decimal(str(detalle.cantidad))
    precio = Decimal(str(detalle.precio_unitario))
    descuento = Decimal(str(getattr(detalle, 'descuento', 0) or 0))
    base_referencial = ((precio - descuento) * cantidad).quantize(Decimal('0.01'))

    if datos['gratuito']:
        impuesto = (
            base_referencial * Decimal(datos['tasa']) / Decimal('100')
        ).quantize(Decimal('0.01'))
        return {
            'codigo': cod,
            'datos': datos,
            # SUNAT 3271/3272: en lineas gratuitas el valor de venta XML es
            # referencial, aunque el importe comercial y pagable sea cero.
            'valor_venta': base_referencial,
            'base_tributaria': base_referencial,
            'impuesto_informado': impuesto,
            'impuesto_total': Decimal('0.00'),
            'precio_alternativo': precio,
            'tipo_precio': '02',
            'valor_unitario': Decimal('0.00'),
        }

    valor_venta = Decimal(str(detalle.subtotal or 0))
    impuesto = Decimal(str(detalle.igv_linea or 0))
    valor_unitario = precio
    precio_alternativo = (
        precio * datos['porcentaje_multiplicador']
    ).quantize(Decimal('0.01'))
    if es_nota_credito:
        valor_unitario = (valor_venta / cantidad).quantize(Decimal('0.0000000001'))
        precio_alternativo = (
            (valor_venta + impuesto) / cantidad
        ).quantize(Decimal('0.0000000001'))

    return {
        'codigo': cod,
        'datos': datos,
        'valor_venta': valor_venta,
        'base_tributaria': valor_venta,
        'impuesto_informado': impuesto,
        'impuesto_total': impuesto,
        'precio_alternativo': precio_alternativo,
        'tipo_precio': '01',
        'valor_unitario': valor_unitario,
    }


def _fix_namespace_prefix(xml_bytes):
    """
    Convierte <ns0:Invoice> a <Invoice xmlns="..."> 
    y asegura que los namespaces de los hijos se preserven correctamente.
    """
    xml_str = xml_bytes.decode('utf-8')
    
    # Reemplazar ns0:Invoice con Invoice y el namespace por defecto
    xml_str = xml_str.replace(
        'xmlns:ns0="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"',
        'xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"'
    )
    xml_str = xml_str.replace('ns0:Invoice', 'Invoice')
    
    return xml_str.encode('utf-8')


def generar_xml_ubl(comprobante):
    """
    Genera XML UBL 2.1 para factura/boleta electronica.
    
    Orden estricto requerido por SUNAT (UBL Invoice 2.1):
    1. UBLExtensions (donde firma digital ds:Signature se inserta en UBLExtensions por firmar.py)
    2. cbc:UBLVersionID
    3. cbc:CustomizationID
    4. cbc:ID
    5. cbc:IssueDate
    6. cbc:IssueTime
    7. cbc:InvoiceTypeCode
    8. cbc:DocumentCurrencyCode
    9. cac:OrderReference (opcional)
    10. cac:Signature
    11. cac:AccountingSupplierParty
    12. cac:AccountingCustomerParty
    13. cac:PaymentTerms
    14. cac:TaxTotal
    15. cac:LegalMonetaryTotal
    16. cac:InvoiceLine (1..N)
    """
    tipo_operacion = _validar_receptor(comprobante)
    moneda = validar_moneda(getattr(comprobante, 'moneda', 'PEN'))

    CAC = NAMESPACES['cac']
    CBC = NAMESPACES['cbc']
    EXT = NAMESPACES['ext']
    DS = NAMESPACES['ds']
    INV = NAMESPACES['inv']
    SAC = NAMESPACES['sac']

    nsmap = {
        'cac': CAC,
        'cbc': CBC,
        'ext': EXT,
        'ds': DS,
        'sac': SAC,
    }

    root = etree.Element(f'{{{INV}}}Invoice', nsmap=nsmap)

    empresa = comprobante.empresa

    # 1. UBLExtensions
    ext_UBLExtensions = etree.SubElement(root, f'{{{EXT}}}UBLExtensions')

    # Extension 1: Para la firma digital (ds:Signature se inserta aqui por firmar.py)
    ext_UBLExtension_sig = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent_sig = etree.SubElement(ext_UBLExtension_sig, f'{{{EXT}}}ExtensionContent')

    # Extension 2: AdditionalInformation requerido por SUNAT (AdditionalMonetaryTotal)
    ext_UBLExtension_add = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent_add = etree.SubElement(ext_UBLExtension_add, f'{{{EXT}}}ExtensionContent')
    sac_AdditionalInfo = etree.SubElement(ext_ExtensionContent_add, f'{{{SAC}}}AdditionalInformation')
    totales_operacion = defaultdict(lambda: Decimal('0'))
    for detalle in comprobante.detalles.all():
        importes = _importes_tributarios_linea(detalle)
        cod = importes['codigo']
        if importes['datos']['gratuito']:
            total_id = '1004'
        else:
            total_id = {'20': '1003', '30': '1002', '40': '1005'}.get(cod, '1001')
        totales_operacion[total_id] += importes['base_tributaria']

    for total_id, total_operacion in sorted(totales_operacion.items()):
        additional_total = etree.SubElement(
            sac_AdditionalInfo, f'{{{SAC}}}AdditionalMonetaryTotal'
        )
        amt_id = etree.SubElement(additional_total, f'{{{CBC}}}ID')
        amt_id.text = total_id
        amt_payable = etree.SubElement(additional_total, f'{{{CBC}}}PayableAmount')
        amt_payable.set('currencyID', moneda)
        amt_payable.text = _money(total_operacion)

    # 2. UBLVersionID
    ubl_version = etree.SubElement(root, f'{{{CBC}}}UBLVersionID')
    ubl_version.text = '2.1'

    # 3. CustomizationID
    customization_id = etree.SubElement(root, f'{{{CBC}}}CustomizationID')
    customization_id.text = '2.0'

    profile_id = etree.SubElement(root, f'{{{CBC}}}ProfileID')
    profile_id.set('schemeName', 'SUNAT:Identificador de Tipo de Operación')
    profile_id.set('schemeAgencyName', 'PE:SUNAT')
    profile_id.set('schemeURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo17')
    profile_id.text = tipo_operacion

    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{comprobante.serie.serie}-{comprobante.numero:08d}"

    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = comprobante.fecha.isoformat()

    tipo_doc = etree.SubElement(root, f'{{{CBC}}}InvoiceTypeCode')
    tipo_doc.set('listAgencyName', 'PE:SUNAT')
    tipo_doc.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01')
    tipo_doc.set('listName', 'Tipo de Documento')
    tipo_doc.set('listID', tipo_operacion)
    tipo_doc.text = comprobante.tipo or (comprobante.serie.tipo if comprobante.serie else '01')

    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.set('listID', 'ISO 4217 Alpha')
    currency_code.set('listName', 'Currency')
    currency_code.set('listAgencyName', 'United Nations Economic Commission for Europe')
    if any(
        _importes_tributarios_linea(det)['datos']['gratuito']
        for det in comprobante.detalles.all()
    ):
        note = etree.Element(f'{{{CBC}}}Note')
        note.set('languageLocaleID', '1002')
        note.text = 'TRANSFERENCIA GRATUITA DE UN BIEN Y/O SERVICIO PRESTADO GRATUITAMENTE'
        tipo_doc.addnext(note)

    currency_code.text = moneda

    line_count = etree.SubElement(root, f'{{{CBC}}}LineCountNumeric')
    line_count.text = str(comprobante.detalles.count())

    signature = etree.SubElement(root, f'{{{CAC}}}Signature')
    sign_id = etree.SubElement(signature, f'{{{CBC}}}ID')
    sign_id.text = 'SignatureSUNAT'
    sign_signatory = etree.SubElement(signature, f'{{{CAC}}}SignatoryParty')
    sign_party_id = etree.SubElement(sign_signatory, f'{{{CAC}}}PartyIdentification')
    sign_party_id_val = etree.SubElement(sign_party_id, f'{{{CBC}}}ID')
    sign_party_id_val.text = empresa.ruc

    party_supplier = etree.SubElement(root, f'{{{CAC}}}AccountingSupplierParty')
    party_supplier_name = etree.SubElement(party_supplier, f'{{{CAC}}}Party')
    
    party_supplier_id = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyIdentification')
    party_supplier_id_val = etree.SubElement(party_supplier_id, f'{{{CBC}}}ID')
    party_supplier_id_val.set('schemeID', '6')
    party_supplier_id_val.text = empresa.ruc
    
    party_name = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyName')
    party_name_val = etree.SubElement(party_name, f'{{{CBC}}}Name')
    party_name_val.text = empresa.razon_social

    party_legal = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyLegalEntity')
    party_reg_name = etree.SubElement(party_legal, f'{{{CBC}}}RegistrationName')
    party_reg_name.text = empresa.razon_social
    
    # SUNAT requiere el código de establecimiento anexo del emisor (AddressTypeCode)
    # Por defecto es '0000' para el local principal.
    party_reg_address = etree.SubElement(party_legal, f'{{{CAC}}}RegistrationAddress')
    address_type_code = etree.SubElement(party_reg_address, f'{{{CBC}}}AddressTypeCode')
    address_type_code.text = '0000'

    customer_party = etree.SubElement(root, f'{{{CAC}}}AccountingCustomerParty')
    customer_party_name = etree.SubElement(customer_party, f'{{{CAC}}}Party')
    
    customer_id = etree.SubElement(customer_party_name, f'{{{CAC}}}PartyIdentification')
    customer_id_val = etree.SubElement(customer_id, f'{{{CBC}}}ID')
    customer_id_val.set('schemeID', TIPO_DOC_MAP.get(comprobante.cliente.tipo_doc, '6'))
    customer_id_val.set('schemeName', 'Documento de Identidad')
    customer_id_val.set('schemeAgencyName', 'PE:SUNAT')
    customer_id_val.set('schemeURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo06')
    customer_id_val.text = comprobante.cliente.num_doc
    
    customer_legal = etree.SubElement(customer_party_name, f'{{{CAC}}}PartyLegalEntity')
    customer_reg_name = etree.SubElement(customer_legal, f'{{{CBC}}}RegistrationName')
    customer_reg_name.text = comprobante.cliente.razon_social

    if tipo_operacion == '0200':
        customer_address = etree.SubElement(customer_legal, f'{{{CAC}}}RegistrationAddress')
        customer_country = etree.SubElement(customer_address, f'{{{CAC}}}Country')
        customer_country_code = etree.SubElement(
            customer_country, f'{{{CBC}}}IdentificationCode'
        )
        customer_country_code.text = comprobante.cliente.pais_codigo.upper()

    # SUNAT requiere indicar la forma de pago (Contado o Crédito). Por defecto: Contado.
    payment_terms = etree.SubElement(root, f'{{{CAC}}}PaymentTerms')
    payment_id = etree.SubElement(payment_terms, f'{{{CBC}}}ID')
    payment_id.text = 'FormaPago'
    payment_means = etree.SubElement(payment_terms, f'{{{CBC}}}PaymentMeansID')
    payment_means.text = 'Contado'

    tax_total = etree.SubElement(root, f'{{{CAC}}}TaxTotal')
    tax_amount = etree.SubElement(tax_total, f'{{{CBC}}}TaxAmount')
    tax_amount.set('currencyID', moneda)
    tax_amount.text = _money(comprobante.igv)

    grupos = defaultdict(lambda: {'base': Decimal('0'), 'igv': Decimal('0')})
    for det in comprobante.detalles.all():
        importes = _importes_tributarios_linea(det)
        cod = importes['codigo']
        grupos[cod]['base'] += importes['base_tributaria']
        grupos[cod]['igv'] += importes['impuesto_informado']

    for cod, grupo in grupos.items():
        datos = obtener_datos_igv(cod)
        ts = etree.SubElement(tax_total, f'{{{CAC}}}TaxSubtotal')
        ts_base = etree.SubElement(ts, f'{{{CBC}}}TaxableAmount')
        ts_base.set('currencyID', moneda)
        ts_base.text = _money(grupo['base'])
        ts_amount = etree.SubElement(ts, f'{{{CBC}}}TaxAmount')
        ts_amount.set('currencyID', moneda)
        ts_amount.text = _money(grupo['igv'])
        ts_item = etree.SubElement(ts, f'{{{CAC}}}TaxCategory')
        ts_item_id = etree.SubElement(ts_item, f'{{{CBC}}}ID')
        ts_item_id.set('schemeID', 'UN/ECE 5305')
        ts_item_id.set('schemeName', 'Tax Category Identifier')
        ts_item_id.set('schemeAgencyName', 'United Nations Economic Commission for Europe')
        ts_item_id.text = datos['categoria']
        ts_item_pct = etree.SubElement(ts_item, f'{{{CBC}}}Percent')
        ts_item_pct.text = datos['tasa']
        ts_scheme = etree.SubElement(ts_item, f'{{{CAC}}}TaxScheme')
        ts_scheme_id = etree.SubElement(ts_scheme, f'{{{CBC}}}ID')
        ts_scheme_id.set('schemeID', 'UN/ECE 5153')
        ts_scheme_id.set('schemeAgencyID', '6')
        ts_scheme_id.text = datos['tributo_id']
        ts_scheme_name = etree.SubElement(ts_scheme, f'{{{CBC}}}Name')
        ts_scheme_name.text = datos['tributo_nombre']
        ts_scheme_type = etree.SubElement(ts_scheme, f'{{{CBC}}}TaxTypeCode')
        ts_scheme_type.text = datos['tributo_tipo']

    legal_total = etree.SubElement(root, f'{{{CAC}}}LegalMonetaryTotal')
    line_extension = etree.SubElement(legal_total, f'{{{CBC}}}LineExtensionAmount')
    line_extension.set('currencyID', moneda)
    line_extension.text = _money(comprobante.subtotal)

    tax_inclusive = etree.SubElement(legal_total, f'{{{CBC}}}TaxInclusiveAmount')
    tax_inclusive.set('currencyID', moneda)
    tax_inclusive.text = _money(comprobante.total)

    payable_amount = etree.SubElement(legal_total, f'{{{CBC}}}PayableAmount')
    payable_amount.set('currencyID', moneda)
    payable_amount.text = _money(comprobante.total)

    for idx, detalle in enumerate(comprobante.detalles.all(), 1):
        importes = _importes_tributarios_linea(detalle)
        invoice_line = etree.SubElement(root, f'{{{CAC}}}InvoiceLine')
        line_id = etree.SubElement(invoice_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        invoiced_quantity = etree.SubElement(invoice_line, f'{{{CBC}}}InvoicedQuantity')
        invoiced_quantity.set('unitCode', UNIDADES_MEDIDA.get(detalle.producto.unidad_medida, 'NIU'))
        invoiced_quantity.text = str(detalle.cantidad)

        line_extension_amount = etree.SubElement(invoice_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', moneda)
        line_extension_amount.text = _money(importes['valor_venta'])

        # Afectacion de la linea de factura
        cod_afectacion_linea = importes['codigo']
        datos_impuesto_linea = importes['datos']

        pricing_ref = etree.SubElement(invoice_line, f'{{{CAC}}}PricingReference')
        alt_price = etree.SubElement(pricing_ref, f'{{{CAC}}}AlternativeConditionPrice')
        alt_price_amount = etree.SubElement(alt_price, f'{{{CBC}}}PriceAmount')
        alt_price_amount.set('currencyID', moneda)
        alt_price_amount.text = (
            _money(importes['precio_alternativo'])
            if importes['tipo_precio'] == '02'
            else str(importes['precio_alternativo'])
        )
        alt_price_type = etree.SubElement(alt_price, f'{{{CBC}}}PriceTypeCode')
        alt_price_type.set('listName', 'Tipo de Precio')
        alt_price_type.set('listAgencyName', 'PE:SUNAT')
        alt_price_type.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16')
        alt_price_type.text = importes['tipo_precio']

        line_tax = etree.SubElement(invoice_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', moneda)
        line_tax_amount.text = _money(importes['impuesto_total'])
        line_tax_subtotal = etree.SubElement(line_tax, f'{{{CAC}}}TaxSubtotal')
        line_tax_subtotal_base = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxableAmount')
        line_tax_subtotal_base.set('currencyID', moneda)
        line_tax_subtotal_base.text = _money(importes['base_tributaria'])
        line_tax_subtotal_amount = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxAmount')
        line_tax_subtotal_amount.set('currencyID', moneda)
        line_tax_subtotal_amount.text = _money(importes['impuesto_informado'])
        
        line_tax_item = etree.SubElement(line_tax_subtotal, f'{{{CAC}}}TaxCategory')
        line_tax_item_id = etree.SubElement(line_tax_item, f'{{{CBC}}}ID')
        line_tax_item_id.set('schemeID', 'UN/ECE 5305')
        line_tax_item_id.set('schemeName', 'Tax Category Identifier')
        line_tax_item_id.set('schemeAgencyName', 'United Nations Economic Commission for Europe')
        line_tax_item_id.text = datos_impuesto_linea['categoria']
        
        line_tax_item_percent = etree.SubElement(line_tax_item, f'{{{CBC}}}Percent')
        line_tax_item_percent.text = datos_impuesto_linea['tasa']
        
        line_tax_exemption = etree.SubElement(line_tax_item, f'{{{CBC}}}TaxExemptionReasonCode')
        line_tax_exemption.set('listAgencyName', 'PE:SUNAT')
        line_tax_exemption.set('listName', 'Afectacion del IGV')
        line_tax_exemption.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07')
        line_tax_exemption.text = str(cod_afectacion_linea)
        
        line_tax_scheme = etree.SubElement(line_tax_item, f'{{{CAC}}}TaxScheme')
        line_tax_scheme_id = etree.SubElement(line_tax_scheme, f'{{{CBC}}}ID')
        line_tax_scheme_id.set('schemeID', 'UN/ECE 5153')
        line_tax_scheme_id.set('schemeAgencyID', '6')
        line_tax_scheme_id.text = datos_impuesto_linea['tributo_id']
        
        line_tax_scheme_name = etree.SubElement(line_tax_scheme, f'{{{CBC}}}Name')
        line_tax_scheme_name.text = datos_impuesto_linea['tributo_nombre']
        
        line_tax_scheme_type = etree.SubElement(line_tax_scheme, f'{{{CBC}}}TaxTypeCode')
        line_tax_scheme_type.text = datos_impuesto_linea['tributo_tipo']

        line_item = etree.SubElement(invoice_line, f'{{{CAC}}}Item')
        line_description = etree.SubElement(line_item, f'{{{CBC}}}Description')
        line_description.text = detalle.producto.descripcion
        line_item_seller = etree.SubElement(line_item, f'{{{CAC}}}SellersItemIdentification')
        line_item_seller_id = etree.SubElement(line_item_seller, f'{{{CBC}}}ID')
        line_item_seller_id.text = getattr(detalle.producto, 'codigo', '001') or '001'

        price = etree.SubElement(invoice_line, f'{{{CAC}}}Price')
        price_amount = etree.SubElement(price, f'{{{CBC}}}PriceAmount')
        price_amount.set('currencyID', moneda)
        price_amount.text = str(importes['valor_unitario'])

    xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')
    
    # Aplicar transformación para remover prefijo ns0 y usar namespace por defecto
    try:
        xml_bytes = _fix_namespace_prefix(xml_bytes)
    except Exception as e:
        logger.warning(f"No se pudo transformar namespace: {e}. Usando XML original.")
    
    return xml_bytes


def firmar_xml(xml_content, empresa_id=None, certificado_id=None):
    """
    Firma el XML UBL usando el certificado digital.
    
    Args:
        xml_content: XML sin firmar (bytes o str)
        empresa_id: ID de la empresa para buscar certificado en BD
        certificado_id: ID especifico del certificado en BD
    
    Returns:
        bytes: XML firmado
    Raises:
        ValueError: Si no se puede firmar el XML
    """
    from .firmar import sign_xml
    return sign_xml(xml_content, empresa_id=empresa_id, certificado_id=certificado_id)


def crear_zip(xml_content, nombre_archivo):
    """
    Crea un ZIP con el XML firmado para enviar a SUNAT.
    
    SUNAT requiere que el ZIP contenga UNICO el archivo XML en la raiz,
    sin directorios adicionales.
    
    Args:
        xml_content: Contenido del XML firmado (bytes o str)
        nombre_archivo: Nombre sin extension (ej: 20103129061-01-F001-00000001)
    
    Returns:
        bytes: Contenido del ZIP
    """
    import zipfile
    from io import BytesIO

    xml_bytes = xml_content if isinstance(xml_content, bytes) else xml_content.encode('utf-8')
    
    if not xml_bytes or len(xml_bytes) == 0:
        raise ValueError("No se puede crear ZIP: el contenido XML esta vacio")
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(nombre_archivo + '.xml', xml_bytes)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


def generar_xml_nota_credito(nota):
    """
    Genera XML UBL 2.1 para Nota de Crédito electrónica.
    """
    referencia = nota.comprobante_referencia
    moneda = validar_moneda(getattr(referencia, 'moneda', 'PEN'))
    tipo_operacion = getattr(referencia, 'tipo_operacion', '0101') or '0101'
    CAC = NAMESPACES['cac']
    CBC = NAMESPACES['cbc']
    EXT = NAMESPACES['ext']
    DS = NAMESPACES['ds']
    SAC = NAMESPACES['sac']
    CN = NAMESPACES['cn']

    nsmap = {
        'cac': CAC,
        'cbc': CBC,
        'ext': EXT,
        'ds': DS,
        'sac': SAC,
    }

    # Raíz es CreditNote
    root = etree.Element(f'{{{CN}}}CreditNote', nsmap=nsmap)
    empresa = nota.comprobante_referencia.empresa

    # 1. UBLExtensions
    ext_UBLExtensions = etree.SubElement(root, f'{{{EXT}}}UBLExtensions')
    
    # Extension 1: Firma
    ext_UBLExtension_sig = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent_sig = etree.SubElement(ext_UBLExtension_sig, f'{{{EXT}}}ExtensionContent')

    # Extension 2: AdditionalInformation
    ext_UBLExtension_add = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent_add = etree.SubElement(ext_UBLExtension_add, f'{{{EXT}}}ExtensionContent')
    sac_AdditionalInfo = etree.SubElement(ext_ExtensionContent_add, f'{{{SAC}}}AdditionalInformation')
    totales_operacion = defaultdict(lambda: Decimal('0'))
    for detalle in nota.detalles.all():
        importes = _importes_tributarios_linea(detalle, es_nota_credito=True)
        cod = importes['codigo']
        if importes['datos']['gratuito']:
            total_id = '1004'
        else:
            total_id = {'20': '1003', '30': '1002', '40': '1005'}.get(cod, '1001')
        totales_operacion[total_id] += importes['base_tributaria']
    for total_id, total_operacion in sorted(totales_operacion.items()):
        additional_total = etree.SubElement(
            sac_AdditionalInfo, f'{{{SAC}}}AdditionalMonetaryTotal'
        )
        amt_id = etree.SubElement(additional_total, f'{{{CBC}}}ID')
        amt_id.text = total_id
        amt_payable = etree.SubElement(additional_total, f'{{{CBC}}}PayableAmount')
        amt_payable.set('currencyID', moneda)
        amt_payable.text = _money(total_operacion)

    # 2. UBLVersionID
    ubl_version = etree.SubElement(root, f'{{{CBC}}}UBLVersionID')
    ubl_version.text = '2.1'

    # 3. CustomizationID
    customization_id = etree.SubElement(root, f'{{{CBC}}}CustomizationID')
    customization_id.text = '2.0'

    # ProfileID
    profile_id = etree.SubElement(root, f'{{{CBC}}}ProfileID')
    profile_id.text = tipo_operacion

    # ID
    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{nota.serie}-{nota.numero:08d}"

    # IssueDate
    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = nota.fecha.isoformat()

    # DocumentCurrencyCode
    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.text = moneda

    if any(
        _importes_tributarios_linea(det, es_nota_credito=True)['datos']['gratuito']
        for det in nota.detalles.all()
    ):
        note = etree.Element(f'{{{CBC}}}Note')
        note.set('languageLocaleID', '1002')
        note.text = 'TRANSFERENCIA GRATUITA DE UN BIEN Y/O SERVICIO PRESTADO GRATUITAMENTE'
        currency_code.addprevious(note)

    # DiscrepancyResponse (Motivo de la Nota)
    discrepancy = etree.SubElement(root, f'{{{CAC}}}DiscrepancyResponse')
    ref_id = etree.SubElement(discrepancy, f'{{{CBC}}}ReferenceID')
    ref_id.text = f"{nota.comprobante_referencia.serie.serie}-{nota.comprobante_referencia.numero:08d}"
    response_code = etree.SubElement(discrepancy, f'{{{CBC}}}ResponseCode')
    response_code.text = nota.tipo_nota # '01', '06', etc.
    desc = etree.SubElement(discrepancy, f'{{{CBC}}}Description')
    desc.text = nota.descripcion or 'ANULACION DE OPERACION'

    # BillingReference (Referencia del documento que se modifica)
    billing_ref = etree.SubElement(root, f'{{{CAC}}}BillingReference')
    inv_doc_ref = etree.SubElement(billing_ref, f'{{{CAC}}}InvoiceDocumentReference')
    inv_id = etree.SubElement(inv_doc_ref, f'{{{CBC}}}ID')
    inv_id.text = f"{nota.comprobante_referencia.serie.serie}-{nota.comprobante_referencia.numero:08d}"
    inv_doc_type = etree.SubElement(inv_doc_ref, f'{{{CBC}}}DocumentTypeCode')
    inv_doc_type.text = nota.comprobante_referencia.tipo

    # Signature
    signature = etree.SubElement(root, f'{{{CAC}}}Signature')
    sign_id = etree.SubElement(signature, f'{{{CBC}}}ID')
    sign_id.text = 'SignatureSUNAT'
    sign_signatory = etree.SubElement(signature, f'{{{CAC}}}SignatoryParty')
    sign_party_id = etree.SubElement(sign_signatory, f'{{{CAC}}}PartyIdentification')
    sign_party_id_val = etree.SubElement(sign_party_id, f'{{{CBC}}}ID')
    sign_party_id_val.text = empresa.ruc

    # Supplier
    party_supplier = etree.SubElement(root, f'{{{CAC}}}AccountingSupplierParty')
    party_supplier_name = etree.SubElement(party_supplier, f'{{{CAC}}}Party')
    
    party_supplier_id = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyIdentification')
    party_supplier_id_val = etree.SubElement(party_supplier_id, f'{{{CBC}}}ID')
    party_supplier_id_val.set('schemeID', '6')
    party_supplier_id_val.text = empresa.ruc
    
    party_name = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyName')
    party_name_val = etree.SubElement(party_name, f'{{{CBC}}}Name')
    party_name_val.text = empresa.razon_social

    party_legal = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyLegalEntity')
    party_reg_name = etree.SubElement(party_legal, f'{{{CBC}}}RegistrationName')
    party_reg_name.text = empresa.razon_social
    
    party_reg_address = etree.SubElement(party_legal, f'{{{CAC}}}RegistrationAddress')
    address_type_code = etree.SubElement(party_reg_address, f'{{{CBC}}}AddressTypeCode')
    address_type_code.text = '0000'

    # Customer
    customer_party = etree.SubElement(root, f'{{{CAC}}}AccountingCustomerParty')
    customer_party_name = etree.SubElement(customer_party, f'{{{CAC}}}Party')
    
    customer_id = etree.SubElement(customer_party_name, f'{{{CAC}}}PartyIdentification')
    customer_id_val = etree.SubElement(customer_id, f'{{{CBC}}}ID')
    customer_id_val.set('schemeID', TIPO_DOC_MAP.get(nota.comprobante_referencia.cliente.tipo_doc, '6'))
    customer_id_val.text = nota.comprobante_referencia.cliente.num_doc
    
    customer_legal = etree.SubElement(customer_party_name, f'{{{CAC}}}PartyLegalEntity')
    customer_reg_name = etree.SubElement(customer_legal, f'{{{CBC}}}RegistrationName')
    customer_reg_name.text = nota.comprobante_referencia.cliente.razon_social
    if tipo_operacion == '0200':
        customer_address = etree.SubElement(customer_legal, f'{{{CAC}}}RegistrationAddress')
        customer_country = etree.SubElement(customer_address, f'{{{CAC}}}Country')
        customer_country_code = etree.SubElement(
            customer_country, f'{{{CBC}}}IdentificationCode'
        )
        customer_country_code.text = referencia.cliente.pais_codigo.upper()

    # TaxTotal
    tax_total = etree.SubElement(root, f'{{{CAC}}}TaxTotal')
    tax_amount = etree.SubElement(tax_total, f'{{{CBC}}}TaxAmount')
    tax_amount.set('currencyID', moneda)
    tax_amount.text = _money(nota.igv)

    grupos = defaultdict(lambda: {'base': Decimal('0'), 'igv': Decimal('0')})
    for det in nota.detalles.all():
        importes = _importes_tributarios_linea(det, es_nota_credito=True)
        cod = importes['codigo']
        grupos[cod]['base'] += importes['base_tributaria']
        grupos[cod]['igv'] += importes['impuesto_informado']

    for cod, grupo in grupos.items():
        datos = obtener_datos_igv(cod)
        ts = etree.SubElement(tax_total, f'{{{CAC}}}TaxSubtotal')
        ts_base = etree.SubElement(ts, f'{{{CBC}}}TaxableAmount')
        ts_base.set('currencyID', moneda)
        ts_base.text = _money(grupo['base'])
        ts_amount = etree.SubElement(ts, f'{{{CBC}}}TaxAmount')
        ts_amount.set('currencyID', moneda)
        ts_amount.text = _money(grupo['igv'])
        ts_item = etree.SubElement(ts, f'{{{CAC}}}TaxCategory')
        ts_item_id = etree.SubElement(ts_item, f'{{{CBC}}}ID')
        ts_item_id.text = datos['categoria']
        ts_item_pct = etree.SubElement(ts_item, f'{{{CBC}}}Percent')
        ts_item_pct.text = datos['tasa']
        ts_scheme = etree.SubElement(ts_item, f'{{{CAC}}}TaxScheme')
        ts_scheme_id = etree.SubElement(ts_scheme, f'{{{CBC}}}ID')
        ts_scheme_id.text = datos['tributo_id']
        ts_scheme_name = etree.SubElement(ts_scheme, f'{{{CBC}}}Name')
        ts_scheme_name.text = datos['tributo_nombre']
        ts_scheme_type = etree.SubElement(ts_scheme, f'{{{CBC}}}TaxTypeCode')
        ts_scheme_type.text = datos['tributo_tipo']

    # LegalMonetaryTotal
    legal_total = etree.SubElement(root, f'{{{CAC}}}LegalMonetaryTotal')
    line_extension = etree.SubElement(legal_total, f'{{{CBC}}}LineExtensionAmount')
    line_extension.set('currencyID', moneda)
    line_extension.text = _money(nota.op_gravada)

    tax_inclusive = etree.SubElement(legal_total, f'{{{CBC}}}TaxInclusiveAmount')
    tax_inclusive.set('currencyID', moneda)
    tax_inclusive.text = _money(nota.importe)

    payable_amount = etree.SubElement(legal_total, f'{{{CBC}}}PayableAmount')
    payable_amount.set('currencyID', moneda)
    payable_amount.text = _money(nota.importe)

    # CreditNoteLines
    for idx, detalle in enumerate(nota.detalles.all(), 1):
        cantidad = Decimal(str(detalle.cantidad))
        if cantidad <= 0:
            raise ValueError(
                f"La cantidad de la linea {idx} de la nota de credito debe ser mayor a cero"
            )

        importes = _importes_tributarios_linea(detalle, es_nota_credito=True)

        credit_line = etree.SubElement(root, f'{{{CAC}}}CreditNoteLine')
        line_id = etree.SubElement(credit_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        cred_quantity = etree.SubElement(credit_line, f'{{{CBC}}}CreditedQuantity')
        cred_quantity.set('unitCode', UNIDADES_MEDIDA.get(detalle.producto.unidad_medida, 'NIU'))
        cred_quantity.text = str(detalle.cantidad)

        cod_afectacion = importes['codigo']
        datos_igv = importes['datos']

        line_extension_amount = etree.SubElement(credit_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', moneda)
        line_extension_amount.text = _money(importes['valor_venta'])

        pricing_ref = etree.SubElement(credit_line, f'{{{CAC}}}PricingReference')
        alt_price = etree.SubElement(pricing_ref, f'{{{CAC}}}AlternativeConditionPrice')
        alt_price_amount = etree.SubElement(alt_price, f'{{{CBC}}}PriceAmount')
        alt_price_amount.set('currencyID', moneda)
        alt_price_amount.text = (
            _money(importes['precio_alternativo'])
            if importes['tipo_precio'] == '02'
            else str(importes['precio_alternativo'])
        )
        alt_price_type = etree.SubElement(alt_price, f'{{{CBC}}}PriceTypeCode')
        alt_price_type.set('listName', 'Tipo de Precio')
        alt_price_type.set('listAgencyName', 'PE:SUNAT')
        alt_price_type.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16')
        alt_price_type.text = importes['tipo_precio']

        line_tax = etree.SubElement(credit_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', moneda)
        line_tax_amount.text = _money(importes['impuesto_total'])
        line_tax_subtotal = etree.SubElement(line_tax, f'{{{CAC}}}TaxSubtotal')
        line_tax_subtotal_base = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxableAmount')
        line_tax_subtotal_base.set('currencyID', moneda)
        line_tax_subtotal_base.text = _money(importes['base_tributaria'])
        line_tax_subtotal_amount = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxAmount')
        line_tax_subtotal_amount.set('currencyID', moneda)
        line_tax_subtotal_amount.text = _money(importes['impuesto_informado'])
        line_tax_item = etree.SubElement(line_tax_subtotal, f'{{{CAC}}}TaxCategory')
        line_tax_item_id = etree.SubElement(line_tax_item, f'{{{CBC}}}ID')
        line_tax_item_id.text = datos_igv['categoria']
        line_tax_item_percent = etree.SubElement(line_tax_item, f'{{{CBC}}}Percent')
        line_tax_item_percent.text = datos_igv['tasa']
        line_tax_exemption = etree.SubElement(line_tax_item, f'{{{CBC}}}TaxExemptionReasonCode')
        line_tax_exemption.set('listAgencyName', 'PE:SUNAT')
        line_tax_exemption.set('listName', 'Afectacion del IGV')
        line_tax_exemption.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07')
        line_tax_exemption.text = str(cod_afectacion)
        line_tax_scheme = etree.SubElement(line_tax_item, f'{{{CAC}}}TaxScheme')
        line_tax_scheme_id = etree.SubElement(line_tax_scheme, f'{{{CBC}}}ID')
        line_tax_scheme_id.text = datos_igv['tributo_id']
        line_tax_scheme_name = etree.SubElement(line_tax_scheme, f'{{{CBC}}}Name')
        line_tax_scheme_name.text = datos_igv['tributo_nombre']
        line_tax_scheme_type = etree.SubElement(line_tax_scheme, f'{{{CBC}}}TaxTypeCode')
        line_tax_scheme_type.text = datos_igv['tributo_tipo']

        line_item = etree.SubElement(credit_line, f'{{{CAC}}}Item')
        line_description = etree.SubElement(line_item, f'{{{CBC}}}Description')
        line_description.text = detalle.producto.descripcion
        line_item_seller = etree.SubElement(line_item, f'{{{CAC}}}SellersItemIdentification')
        line_item_seller_id = etree.SubElement(line_item_seller, f'{{{CBC}}}ID')
        line_item_seller_id.text = getattr(detalle.producto, 'codigo', '001') or '001'

        price = etree.SubElement(credit_line, f'{{{CAC}}}Price')
        price_amount = etree.SubElement(price, f'{{{CBC}}}PriceAmount')
        price_amount.set('currencyID', moneda)
        price_amount.text = str(importes['valor_unitario'])

    xml_bytes = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    try:
        xml_str = xml_bytes.decode('utf-8')
        xml_str = xml_str.replace(
            f'xmlns:ns0="{CN}"',
            f'xmlns="{CN}"'
        )
        xml_str = xml_str.replace('ns0:CreditNote', 'CreditNote')
        xml_bytes = xml_str.encode('utf-8')
    except Exception as e:
        logger.warning(f"No se pudo transformar namespace de Nota de Credito: {e}")

    return xml_bytes
