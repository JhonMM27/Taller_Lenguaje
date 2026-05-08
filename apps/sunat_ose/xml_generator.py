import logging
from lxml import etree
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)

NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'inv': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
}

TIPO_DOC_MAP = {
    '1': '1',
    '6': '6',
    '4': '4',
    '7': '7',
    'A': '1',
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
    'UNI': 'UNI',
    'KG': 'KGM',
    'UND': 'UND',
    'Caja': 'CJA',
    'Paquete': 'PAQ',
    'Litro': 'LTR',
}


def generar_xml_ubl(comprobante):
    CAC = NAMESPACES['cac']
    CBC = NAMESPACES['cbc']
    EXT = NAMESPACES['ext']
    DS = NAMESPACES['ds']
    INV = NAMESPACES['inv']

    nsmap = {
        'cac': CAC,
        'cbc': CBC,
        'ext': EXT,
        'ds': DS,
    }

    root = etree.Element(f'{{{INV}}}Invoice', nsmap=nsmap)

    empresa = comprobante.empresa

    ext_UBLExtensions = etree.SubElement(root, f'{{{EXT}}}UBLExtensions')
    ext_UBLExtension = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent = etree.SubElement(ext_UBLExtension, f'{{{EXT}}}ExtensionContent')

    ubl_version = etree.SubElement(root, f'{{{CBC}}}UBLVersionID')
    ubl_version.text = '2.1'

    customization_id = etree.SubElement(root, f'{{{CBC}}}CustomizationID')
    customization_id.set('schemeID', 'urn:oasis:names:specification:ubl:codelist:profile:ID')
    customization_id.text = '2.0'

    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{comprobante.serie.serie}-{comprobante.numero:08d}"

    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = comprobante.fecha.isoformat()

    hora_emision = etree.SubElement(root, f'{{{CBC}}}IssueTime')
    hora_emision.text = '00:00:00'

    fecha_vencimiento = etree.SubElement(root, f'{{{CBC}}}DueDate')
    fecha_vencimiento.text = comprobante.fecha.isoformat()

    tipo_doc = etree.SubElement(root, f'{{{CBC}}}InvoiceTypeCode')
    tipo_doc.set('listAgencyName', 'PE:SUNAT')
    tipo_doc.set('listURI', 'urn:pe:sunat:catalog:01')
    tipo_doc.text = comprobante.tipo

    if comprobante.tipo == '03':
        tipo_doc.set('listName', 'Tipo de Documento')
        tipo_doc.set('listID', '0101')
    elif comprobante.tipo == '01':
        tipo_doc.set('listName', 'Tipo de Documento')
        tipo_doc.set('listID', '0101')

    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.set('listID', 'ISO 4217 Alpha')
    currency_code.set('listName', 'Currency')
    currency_code.text = 'PEN'

    signature = etree.SubElement(root, f'{{{CAC}}}Signature')
    sign_id = etree.SubElement(signature, f'{{{CBC}}}ID')
    sign_id.text = 'SignatureSUNAT'
    sign_signatory = etree.SubElement(signature, f'{{{CAC}}}SignatoryParty')
    sign_party_id = etree.SubElement(sign_signatory, f'{{{CAC}}}PartyIdentification')
    sign_party_id_val = etree.SubElement(sign_party_id, f'{{{CBC}}}ID')
    sign_party_id_val.text = empresa.ruc
    sign_party_name = etree.SubElement(sign_signatory, f'{{{CAC}}}PartyName')
    sign_party_name_val = etree.SubElement(sign_party_name, f'{{{CBC}}}Name')
    sign_party_name_val.text = empresa.razon_social
    sign_digital_signon = etree.SubElement(signature, f'{{{CAC}}}DigitalSignatureAttachment')
    sign_digital_ref = etree.SubElement(sign_digital_signon, f'{{{CAC}}}ExternalReference')
    sign_digital_uri = etree.SubElement(sign_digital_ref, f'{{{CBC}}}URI')
    sign_digital_uri.text = '#SignatureSUNAT'

    party_supplier = etree.SubElement(root, f'{{{CAC}}}AccountingSupplierParty')
    party_sup_party = etree.SubElement(party_supplier, f'{{{CAC}}}Party')
    
    party_sup_id = etree.SubElement(party_sup_party, f'{{{CAC}}}PartyIdentification')
    party_sup_id_val = etree.SubElement(party_sup_id, f'{{{CBC}}}ID')
    party_sup_id_val.set('schemeID', '6')
    party_sup_id_val.text = empresa.ruc

    party_sup_name = etree.SubElement(party_sup_party, f'{{{CAC}}}PartyName')
    party_sup_name_val = etree.SubElement(party_sup_name, f'{{{CBC}}}Name')
    party_sup_name_val.text = empresa.razon_social

    party_sup_legal = etree.SubElement(party_sup_party, f'{{{CAC}}}PartyLegalEntity')
    party_sup_reg_name = etree.SubElement(party_sup_legal, f'{{{CBC}}}RegistrationName')
    party_sup_reg_name.text = empresa.razon_social
    
    party_sup_addr = etree.SubElement(party_sup_legal, f'{{{CAC}}}RegistrationAddress')
    party_sup_addr_id = etree.SubElement(party_sup_addr, f'{{{CBC}}}ID')
    party_sup_addr_id.text = getattr(empresa, 'ubigeo', None) or '150101'
    
    party_sup_addr_code = etree.SubElement(party_sup_addr, f'{{{CBC}}}AddressTypeCode')
    party_sup_addr_code.text = '0000'
    party_sup_addr_street = etree.SubElement(party_sup_addr, f'{{{CBC}}}StreetName')
    party_sup_addr_street.text = getattr(empresa, 'direccion', None) or 'SN'
    party_sup_addr_city = etree.SubElement(party_sup_addr, f'{{{CBC}}}CityName')
    party_sup_addr_city.text = getattr(empresa, 'ciudad', None) or 'LIMA'
    party_sup_addr_dist = etree.SubElement(party_sup_addr, f'{{{CBC}}}District')
    party_sup_addr_dist.text = getattr(empresa, 'distrito', None) or ''
    party_sup_addr_country = etree.SubElement(party_sup_addr, f'{{{CAC}}}Country')
    party_sup_addr_country_id = etree.SubElement(party_sup_addr_country, f'{{{CBC}}}IdentificationCode')
    party_sup_addr_country_id.set('listID', 'ISO 3166-1')
    party_sup_addr_country_id.set('listAgencyID', 'United Nations Economic Commission for Europe')
    party_sup_addr_country_id.text = 'PE'

    customer_party = etree.SubElement(root, f'{{{CAC}}}AccountingCustomerParty')
    customer_party_party = etree.SubElement(customer_party, f'{{{CAC}}}Party')
    
    customer_id = etree.SubElement(customer_party_party, f'{{{CAC}}}PartyIdentification')
    customer_id_val = etree.SubElement(customer_id, f'{{{CBC}}}ID')
    customer_id_val.set('schemeID', TIPO_DOC_MAP.get(comprobante.cliente.tipo_doc, '6'))
    customer_id_val.text = comprobante.cliente.num_doc

    customer_name = etree.SubElement(customer_party_party, f'{{{CAC}}}PartyName')
    customer_name_val = etree.SubElement(customer_name, f'{{{CBC}}}Name')
    customer_name_val.text = comprobante.cliente.razon_social

    customer_legal = etree.SubElement(customer_party_party, f'{{{CAC}}}PartyLegalEntity')
    customer_reg_name = etree.SubElement(customer_legal, f'{{{CBC}}}RegistrationName')
    customer_reg_name.text = comprobante.cliente.razon_social

    # Forma de Pago (MANDATORIO en UBL 2.1)
    payment_terms = etree.SubElement(root, f'{{{CAC}}}PaymentTerms')
    payment_terms_id = etree.SubElement(payment_terms, f'{{{CBC}}}ID')
    payment_terms_id.text = 'FormaPago'
    payment_terms_means = etree.SubElement(payment_terms, f'{{{CBC}}}PaymentMeansID')
    payment_terms_means.text = 'Contado'

    if hasattr(comprobante, 'orden_compra') and comprobante.orden_compra:
        orden_compra = etree.SubElement(root, f'{{{CBC}}}OrderReference')
        orden_compra_id = etree.SubElement(orden_compra, f'{{{CBC}}}ID')
        orden_compra_id.text = comprobante.orden_compra

    tax_total = etree.SubElement(root, f'{{{CAC}}}TaxTotal')
    tax_amount = etree.SubElement(tax_total, f'{{{CBC}}}TaxAmount')
    tax_amount.set('currencyID', 'PEN')
    tax_amount.text = str(comprobante.igv)

    tax_subtotal = etree.SubElement(tax_total, f'{{{CAC}}}TaxSubtotal')
    tax_subtotal_base = etree.SubElement(tax_subtotal, f'{{{CBC}}}TaxableAmount')
    tax_subtotal_base.set('currencyID', 'PEN')
    tax_subtotal_base.text = str(comprobante.subtotal)
    
    tax_subtotal_amount = etree.SubElement(tax_subtotal, f'{{{CBC}}}TaxAmount')
    tax_subtotal_amount.set('currencyID', 'PEN')
    tax_subtotal_amount.text = str(comprobante.igv)

    tax_subtotal_item = etree.SubElement(tax_subtotal, f'{{{CAC}}}TaxCategory')
    tax_subtotal_item_id = etree.SubElement(tax_subtotal_item, f'{{{CBC}}}ID')
    tax_subtotal_item_id.set('schemeID', 'UN/ECE 5305')
    tax_subtotal_item_id.text = 'S'
    
    tax_subtotal_percent = etree.SubElement(tax_subtotal_item, f'{{{CBC}}}Percent')
    tax_subtotal_percent.text = '18.00'

    tax_subtotal_name = etree.SubElement(tax_subtotal_item, f'{{{CAC}}}TaxScheme')
    tax_subtotal_name_id = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}ID')
    tax_subtotal_name_id.set('schemeID', 'UN/ECE 5305')
    tax_subtotal_name_id.text = '1000'
    tax_subtotal_name_name = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}Name')
    tax_subtotal_name_name.text = 'IGV'
    tax_subtotal_name_type = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}TaxTypeCode')
    tax_subtotal_name_type.text = 'VAT'

    legal_total = etree.SubElement(root, f'{{{CAC}}}LegalMonetaryTotal')
    line_extension = etree.SubElement(legal_total, f'{{{CBC}}}LineExtensionAmount')
    line_extension.set('currencyID', 'PEN')
    line_extension.text = str(comprobante.subtotal)

    tax_inclusive = etree.SubElement(legal_total, f'{{{CBC}}}TaxInclusiveAmount')
    tax_inclusive.set('currencyID', 'PEN')
    tax_inclusive.text = str(comprobante.total)

    payable_amount = etree.SubElement(legal_total, f'{{{CBC}}}PayableAmount')
    payable_amount.set('currencyID', 'PEN')
    payable_amount.text = str(comprobante.total)

    for idx, detalle in enumerate(comprobante.detalles.all(), 1):
        # Cada línea del comprobante (InvoiceLine) contiene los datos del producto/servicio
        invoice_line = etree.SubElement(root, f'{{{CAC}}}InvoiceLine')
        line_id = etree.SubElement(invoice_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        invoiced_quantity = etree.SubElement(invoice_line, f'{{{CBC}}}InvoicedQuantity')
        invoiced_quantity.set('unitCode', detalle.producto.unidad_medida or 'UNI')
        invoiced_quantity.text = str(detalle.cantidad)

        line_extension_amount = etree.SubElement(invoice_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', 'PEN')
        line_extension_amount.text = str(detalle.subtotal)

        # Referencia de precio (PricingReference)
        pricing_reference = etree.SubElement(invoice_line, f'{{{CAC}}}PricingReference')
        line_price = etree.SubElement(pricing_reference, f'{{{CAC}}}AlternativeConditionPrice')
        line_price_amount = etree.SubElement(line_price, f'{{{CBC}}}PriceAmount')
        line_price_amount.set('currencyID', 'PEN')
        # El precio referencial (01) debe incluir impuestos
        precio_con_igv = detalle.precio_unitario * Decimal('1.18')
        line_price_amount.text = f"{precio_con_igv:.2f}"
        line_price_type = etree.SubElement(line_price, f'{{{CBC}}}PriceTypeCode')
        line_price_type.text = '01'

        # Impuesto total de la línea (TaxTotal)
        line_tax = etree.SubElement(invoice_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', 'PEN')
        line_tax_amount.text = str(detalle.igv_linea or '0.00')

        line_tax_item = etree.SubElement(line_tax, f'{{{CAC}}}TaxSubtotal')
        line_tax_base = etree.SubElement(line_tax_item, f'{{{CBC}}}TaxableAmount')
        line_tax_base.set('currencyID', 'PEN')
        line_tax_base.text = str(detalle.subtotal)
        
        line_tax_item_amount = etree.SubElement(line_tax_item, f'{{{CBC}}}TaxAmount')
        line_tax_item_amount.set('currencyID', 'PEN')
        line_tax_item_amount.text = str(detalle.igv_linea or '0.00')

        line_tax_category = etree.SubElement(line_tax_item, f'{{{CAC}}}TaxCategory')
        line_tax_category_id = etree.SubElement(line_tax_category, f'{{{CBC}}}ID')
        line_tax_category_id.set('schemeID', 'UN/ECE 5305')
        line_tax_category_id.text = 'S'
        
        line_tax_percent = etree.SubElement(line_tax_category, f'{{{CBC}}}Percent')
        line_tax_percent.text = '18.00'

        cod_afectacion = getattr(detalle, 'cod_tipo_afectacion', '10')
        tax_exemption = etree.SubElement(line_tax_category, f'{{{CBC}}}TaxExemptionReasonCode')
        tax_exemption.set('listAgencyName', 'PE:SUNAT')
        tax_exemption.set('listURI', 'urn:pe:sunat:catalog:07')
        tax_exemption.text = cod_afectacion

        line_tax_scheme = etree.SubElement(line_tax_category, f'{{{CAC}}}TaxScheme')
        line_tax_scheme_id = etree.SubElement(line_tax_scheme, f'{{{CBC}}}ID')
        line_tax_scheme_id.set('schemeID', 'UN/ECE 5305')
        line_tax_scheme_id.text = '1000'
        line_tax_scheme_name = etree.SubElement(line_tax_scheme, f'{{{CBC}}}Name')
        line_tax_scheme_name.text = 'IGV'
        line_tax_scheme_type = etree.SubElement(line_tax_scheme, f'{{{CBC}}}TaxTypeCode')
        line_tax_scheme_type.text = 'VAT'

        # Datos del producto (Item)
        line_item = etree.SubElement(invoice_line, f'{{{CAC}}}Item')
        line_description = etree.SubElement(line_item, f'{{{CBC}}}Description')
        line_description.text = detalle.producto.descripcion

        line_sellers_id = etree.SubElement(line_item, f'{{{CAC}}}SellersItemIdentification')
        line_sellers_id_val = etree.SubElement(line_sellers_id, f'{{{CBC}}}ID')
        line_sellers_id_val.text = detalle.producto.codigo

        # Precio unitario (Price) - Hijo de InvoiceLine, después de Item
        price = etree.SubElement(invoice_line, f'{{{CAC}}}Price')
        price_amount = etree.SubElement(price, f'{{{CBC}}}PriceAmount')
        price_amount.set('currencyID', 'PEN')
        price_amount.text = str(detalle.precio_unitario)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')


def generar_nota_credito_xml(nota):
    from apps.notas_credito.models import NotaCredito
    
    # Variables locales con los URIs de namespaces para usar en formato {uri}localname
    CAC = NAMESPACES['cac']
    CBC = NAMESPACES['cbc']
    EXT = NAMESPACES['ext']
    
    root = etree.Element(f'{{{CAC}}}CreditNote')

    empresa = nota.empresa

    ext_UBLExtensions = etree.SubElement(root, f'{{{EXT}}}UBLExtensions')
    ext_UBLExtension = etree.SubElement(ext_UBLExtensions, f'{{{EXT}}}UBLExtension')
    ext_ExtensionContent = etree.SubElement(ext_UBLExtension, f'{{{EXT}}}ExtensionContent')

    ubl_version = etree.SubElement(root, f'{{{CBC}}}UBLVersionID')
    ubl_version.text = '2.1'

    customization_id = etree.SubElement(root, f'{{{CBC}}}CustomizationID')
    customization_id.text = '2.0'

    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{nota.serie}-{nota.numero:08d}"

    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = nota.fecha.isoformat()

    tipo_doc = etree.SubElement(root, f'{{{CBC}}}CreditNoteTypeCode')
    tipo_doc.set('listAgencyName', 'PE:SUNAT')
    tipo_doc.set('listURI', 'urn:pe:sunat:catalog:07')
    tipo_doc.text = nota.tipo_nota

    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.set('listID', 'ISO 4217 Alpha')
    currency_code.text = 'PEN'

    signature = etree.SubElement(root, f'{{{CAC}}}Signature')
    sign_id = etree.SubElement(signature, f'{{{CBC}}}ID')
    sign_id.text = 'SignatureSUNAT'
    sign_signatory = etree.SubElement(signature, f'{{{CAC}}}SignatoryParty')
    sign_party_id = etree.SubElement(sign_signatory, f'{{{CAC}}}PartyIdentification')
    sign_party_id_val = etree.SubElement(sign_party_id, f'{{{CBC}}}ID')
    sign_party_id_val.text = empresa.ruc

    party_supplier = etree.SubElement(root, f'{{{CAC}}}AccountingSupplierParty')
    party_supplier_id = etree.SubElement(party_supplier, f'{{{CBC}}}CustomerAssignedAccountID')
    party_supplier_id.text = empresa.ruc
    party_supplier_add = etree.SubElement(party_supplier, f'{{{CBC}}}AdditionalAccountID')
    party_supplier_add.text = '6'

    party_supplier_name = etree.SubElement(party_supplier, f'{{{CAC}}}Party')
    party_name = etree.SubElement(party_supplier_name, f'{{{CAC}}}PartyName')
    party_name_val = etree.SubElement(party_name, f'{{{CBC}}}Name')
    party_name_val.text = empresa.razon_social

    customer_party = etree.SubElement(root, f'{{{CAC}}}AccountingCustomerParty')
    customer_id = etree.SubElement(customer_party, f'{{{CBC}}}CustomerAssignedAccountID')
    customer_id.text = nota.cliente.num_doc
    customer_add = etree.SubElement(customer_party, f'{{{CBC}}}AdditionalAccountID')
    customer_add.text = TIPO_DOC_MAP.get(nota.cliente.tipo_doc, '6')

    billing_reference = etree.SubElement(root, f'{{{CAC}}}BillingReference')
    invoice_doc_ref = etree.SubElement(billing_reference, f'{{{CAC}}}InvoiceDocumentReference')
    invoice_doc_ref_id = etree.SubElement(invoice_doc_ref, f'{{{CBC}}}ID')
    invoice_doc_ref_id.text = nota.comprobante.numero
    invoice_doc_ref_type = etree.SubElement(invoice_doc_ref, f'{{{CBC}}}DocumentTypeCode')
    invoice_doc_ref_type.text = nota.comprobante.tipo

    tax_total = etree.SubElement(root, f'{{{CAC}}}TaxTotal')
    tax_amount = etree.SubElement(tax_total, f'{{{CBC}}}TaxAmount')
    tax_amount.set('currencyID', 'PEN')
    tax_amount.text = str(nota.igv)

    tax_subtotal = etree.SubElement(tax_total, f'{{{CAC}}}TaxSubtotal')
    tax_subtotal_amount = etree.SubElement(tax_subtotal, f'{{{CBC}}}TaxAmount')
    tax_subtotal_amount.set('currencyID', 'PEN')
    tax_subtotal_amount.text = str(nota.igv)

    legal_total = etree.SubElement(root, f'{{{CAC}}}LegalMonetaryTotal')
    line_extension = etree.SubElement(legal_total, f'{{{CBC}}}LineExtensionAmount')
    line_extension.set('currencyID', 'PEN')
    line_extension.text = str(nota.subtotal)

    payable_amount = etree.SubElement(legal_total, f'{{{CBC}}}PayableAmount')
    payable_amount.set('currencyID', 'PEN')
    payable_amount.text = str(nota.total)

    for idx, detalle in enumerate(nota.detalles.all(), 1):
        credit_line = etree.SubElement(root, f'{{{CAC}}}CreditNoteLine')
        line_id = etree.SubElement(credit_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        credited_quantity = etree.SubElement(credit_line, f'{{{CBC}}}CreditedQuantity')
        credited_quantity.set('unitCode', detalle.producto.unidad_medida or 'UNI')
        credited_quantity.text = str(detalle.cantidad)

        line_extension_amount = etree.SubElement(credit_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', 'PEN')
        line_extension_amount.text = str(detalle.subtotal)

        line_tax = etree.SubElement(credit_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', 'PEN')
        line_tax_amount.text = str(detalle.igv_linea or '0.00')

        line_item = etree.SubElement(credit_line, f'{{{CAC}}}Item')
        line_description = etree.SubElement(line_item, f'{{{CBC}}}Description')
        line_description.text = detalle.producto.descripcion

        price = etree.SubElement(line_item, f'{{{CAC}}}Price')
        price_amount = etree.SubElement(price, f'{{{CBC}}}PriceAmount')
        price_amount.set('currencyID', 'PEN')
        price_amount.text = str(detalle.precio_unitario)

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8')


def firmar_xml(xml_content):
    from .firmar import sign_xml
    return sign_xml(xml_content)


def crear_zip(xml_content, nombre_archivo):
    import zipfile
    from io import BytesIO

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(nombre_archivo + '.xml', xml_content)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()