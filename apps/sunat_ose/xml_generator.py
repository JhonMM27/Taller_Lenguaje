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
    'sac': 'urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1',
    'cn': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
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
    """
    Retorna un diccionario con los datos del impuesto correspondientes al codigo de afectacion de la SUNAT:
    tasa, tax_category_id, tributo_id, tributo_nombre, tributo_tipo, porcentaje_multiplicador
    """
    cod = str(cod_afectacion)
    
    # Gravado (Operación Onerosa)
    if cod.startswith('1') and cod not in ['17']:
        return {
            'tasa': '18.00',
            'categoria': 'S',
            'tributo_id': '1000',
            'tributo_nombre': 'IGV',
            'tributo_tipo': 'VAT',
            'porcentaje_multiplicador': 1.18
        }
    # Exonerado
    elif cod.startswith('2'):
        return {
            'tasa': '0.00',
            'categoria': 'E',
            'tributo_id': '9997',
            'tributo_nombre': 'EXO',
            'tributo_tipo': 'VAT',
            'porcentaje_multiplicador': 1.00
        }
    # Inafecto
    elif cod.startswith('3') or cod == '17':
        return {
            'tasa': '0.00',
            'categoria': 'O',
            'tributo_id': '9998',
            'tributo_nombre': 'INA',
            'tributo_tipo': 'FRE',
            'porcentaje_multiplicador': 1.00
        }
    # Exportación
    elif cod.startswith('4'):
        return {
            'tasa': '0.00',
            'categoria': 'G',
            'tributo_id': '9995',
            'tributo_nombre': 'EXP',
            'tributo_tipo': 'FRE',
            'porcentaje_multiplicador': 1.00
        }
    # Otros
    else:
        return {
            'tasa': '0.00',
            'categoria': 'O',
            'tributo_id': '9999',
            'tributo_nombre': 'OTROS',
            'tributo_tipo': 'OTH',
            'porcentaje_multiplicador': 1.00
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
    sac_AdditionalMonetaryTotal = etree.SubElement(sac_AdditionalInfo, f'{{{SAC}}}AdditionalMonetaryTotal')
    amt_id = etree.SubElement(sac_AdditionalMonetaryTotal, f'{{{CBC}}}ID')
    amt_id.text = '1001'
    amt_payable = etree.SubElement(sac_AdditionalMonetaryTotal, f'{{{CBC}}}PayableAmount')
    amt_payable.set('currencyID', 'PEN')
    amt_payable.text = str(comprobante.subtotal)

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
    profile_id.text = '0101'

    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{comprobante.serie.serie}-{comprobante.numero:08d}"

    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = comprobante.fecha.isoformat()

    tipo_doc = etree.SubElement(root, f'{{{CBC}}}InvoiceTypeCode')
    tipo_doc.set('listAgencyName', 'PE:SUNAT')
    tipo_doc.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01')
    tipo_doc.set('listName', 'Tipo de Documento')
    tipo_doc.set('listID', '0101')
    tipo_doc.text = comprobante.tipo or (comprobante.serie.tipo if comprobante.serie else '01')

    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.set('listID', 'ISO 4217 Alpha')
    currency_code.set('listName', 'Currency')
    currency_code.set('listAgencyName', 'United Nations Economic Commission for Europe')
    currency_code.text = 'PEN'

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
    customer_id_val.text = comprobante.cliente.num_doc
    
    customer_legal = etree.SubElement(customer_party_name, f'{{{CAC}}}PartyLegalEntity')
    customer_reg_name = etree.SubElement(customer_legal, f'{{{CBC}}}RegistrationName')
    customer_reg_name.text = comprobante.cliente.razon_social

    # SUNAT requiere indicar la forma de pago (Contado o Crédito). Por defecto: Contado.
    payment_terms = etree.SubElement(root, f'{{{CAC}}}PaymentTerms')
    payment_id = etree.SubElement(payment_terms, f'{{{CBC}}}ID')
    payment_id.text = 'FormaPago'
    payment_means = etree.SubElement(payment_terms, f'{{{CBC}}}PaymentMeansID')
    payment_means.text = 'Contado'

    # Obtener afectacion predominante para la cabecera
    primer_detalle = comprobante.detalles.first()
    cod_afectacion_cabecera = '10'
    if primer_detalle:
        cod_afectacion_cabecera = getattr(primer_detalle.producto, 'cod_tipo_afectacion', '10') or '10'
    
    datos_impuesto_cabecera = obtener_datos_igv(cod_afectacion_cabecera)

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
    tax_subtotal_item_id.set('schemeName', 'Tax Category Identifier')
    tax_subtotal_item_id.set('schemeAgencyName', 'United Nations Economic Commission for Europe')
    tax_subtotal_item_id.text = datos_impuesto_cabecera['categoria']
    
    tax_subtotal_percent = etree.SubElement(tax_subtotal_item, f'{{{CBC}}}Percent')
    tax_subtotal_percent.text = datos_impuesto_cabecera['tasa']
    
    tax_subtotal_name = etree.SubElement(tax_subtotal_item, f'{{{CAC}}}TaxScheme')
    tax_subtotal_name_id = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}ID')
    tax_subtotal_name_id.set('schemeID', 'UN/ECE 5153')
    tax_subtotal_name_id.set('schemeAgencyID', '6')
    tax_subtotal_name_id.text = datos_impuesto_cabecera['tributo_id']
    
    tax_subtotal_name_name = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}Name')
    tax_subtotal_name_name.text = datos_impuesto_cabecera['tributo_nombre']
    
    tax_subtotal_name_type = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}TaxTypeCode')
    tax_subtotal_name_type.text = datos_impuesto_cabecera['tributo_tipo']

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
        invoice_line = etree.SubElement(root, f'{{{CAC}}}InvoiceLine')
        line_id = etree.SubElement(invoice_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        invoiced_quantity = etree.SubElement(invoice_line, f'{{{CBC}}}InvoicedQuantity')
        invoiced_quantity.set('unitCode', UNIDADES_MEDIDA.get(detalle.producto.unidad_medida, 'NIU'))
        invoiced_quantity.text = str(detalle.cantidad)

        line_extension_amount = etree.SubElement(invoice_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', 'PEN')
        line_extension_amount.text = str(detalle.subtotal)

        # Afectacion de la linea de factura
        cod_afectacion_linea = getattr(detalle.producto, 'cod_tipo_afectacion', '10') or '10'
        datos_impuesto_linea = obtener_datos_igv(cod_afectacion_linea)

        pricing_ref = etree.SubElement(invoice_line, f'{{{CAC}}}PricingReference')
        alt_price = etree.SubElement(pricing_ref, f'{{{CAC}}}AlternativeConditionPrice')
        alt_price_amount = etree.SubElement(alt_price, f'{{{CBC}}}PriceAmount')
        alt_price_amount.set('currencyID', 'PEN')
        alt_price_amount.text = str(round(float(detalle.precio_unitario) * datos_impuesto_linea['porcentaje_multiplicador'], 2))
        alt_price_type = etree.SubElement(alt_price, f'{{{CBC}}}PriceTypeCode')
        alt_price_type.set('listName', 'Tipo de Precio')
        alt_price_type.set('listAgencyName', 'PE:SUNAT')
        alt_price_type.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16')
        alt_price_type.text = '01'

        line_tax = etree.SubElement(invoice_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', 'PEN')
        line_tax_amount.text = str(detalle.igv_linea or '0.00')
        line_tax_subtotal = etree.SubElement(line_tax, f'{{{CAC}}}TaxSubtotal')
        line_tax_subtotal_base = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxableAmount')
        line_tax_subtotal_base.set('currencyID', 'PEN')
        line_tax_subtotal_base.text = str(detalle.subtotal)
        line_tax_subtotal_amount = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxAmount')
        line_tax_subtotal_amount.set('currencyID', 'PEN')
        line_tax_subtotal_amount.text = str(detalle.igv_linea or '0.00')
        
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
        price_amount.set('currencyID', 'PEN')
        price_amount.text = str(detalle.precio_unitario)

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
    sac_AdditionalMonetaryTotal = etree.SubElement(sac_AdditionalInfo, f'{{{SAC}}}AdditionalMonetaryTotal')
    amt_id = etree.SubElement(sac_AdditionalMonetaryTotal, f'{{{CBC}}}ID')
    amt_id.text = '1001'
    amt_payable = etree.SubElement(sac_AdditionalMonetaryTotal, f'{{{CBC}}}PayableAmount')
    amt_payable.set('currencyID', 'PEN')
    amt_payable.text = str(nota.op_gravada)

    # 2. UBLVersionID
    ubl_version = etree.SubElement(root, f'{{{CBC}}}UBLVersionID')
    ubl_version.text = '2.1'

    # 3. CustomizationID
    customization_id = etree.SubElement(root, f'{{{CBC}}}CustomizationID')
    customization_id.text = '2.0'

    # ProfileID
    profile_id = etree.SubElement(root, f'{{{CBC}}}ProfileID')
    profile_id.text = '0101'

    # ID
    num_doc = etree.SubElement(root, f'{{{CBC}}}ID')
    num_doc.text = f"{nota.serie}-{nota.numero:08d}"

    # IssueDate
    fecha_emision = etree.SubElement(root, f'{{{CBC}}}IssueDate')
    fecha_emision.text = nota.fecha.isoformat()

    # DocumentCurrencyCode
    currency_code = etree.SubElement(root, f'{{{CBC}}}DocumentCurrencyCode')
    currency_code.text = 'PEN'

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

    # TaxTotal
    tax_total = etree.SubElement(root, f'{{{CAC}}}TaxTotal')
    tax_amount = etree.SubElement(tax_total, f'{{{CBC}}}TaxAmount')
    tax_amount.set('currencyID', 'PEN')
    tax_amount.text = str(nota.igv)

    tax_subtotal = etree.SubElement(tax_total, f'{{{CAC}}}TaxSubtotal')
    tax_subtotal_base = etree.SubElement(tax_subtotal, f'{{{CBC}}}TaxableAmount')
    tax_subtotal_base.set('currencyID', 'PEN')
    tax_subtotal_base.text = str(nota.op_gravada)
    tax_subtotal_amount = etree.SubElement(tax_subtotal, f'{{{CBC}}}TaxAmount')
    tax_subtotal_amount.set('currencyID', 'PEN')
    tax_subtotal_amount.text = str(nota.igv)
    
    tax_subtotal_item = etree.SubElement(tax_subtotal, f'{{{CAC}}}TaxCategory')
    tax_subtotal_item_id = etree.SubElement(tax_subtotal_item, f'{{{CBC}}}ID')
    tax_subtotal_item_id.text = 'S'
    tax_subtotal_percent = etree.SubElement(tax_subtotal_item, f'{{{CBC}}}Percent')
    tax_subtotal_percent.text = '18.00'
    
    tax_subtotal_name = etree.SubElement(tax_subtotal_item, f'{{{CAC}}}TaxScheme')
    tax_subtotal_name_id = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}ID')
    tax_subtotal_name_id.text = '1000'
    tax_subtotal_name_name = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}Name')
    tax_subtotal_name_name.text = 'IGV'
    tax_subtotal_name_type = etree.SubElement(tax_subtotal_name, f'{{{CBC}}}TaxTypeCode')
    tax_subtotal_name_type.text = 'VAT'

    # LegalMonetaryTotal
    legal_total = etree.SubElement(root, f'{{{CAC}}}LegalMonetaryTotal')
    line_extension = etree.SubElement(legal_total, f'{{{CBC}}}LineExtensionAmount')
    line_extension.set('currencyID', 'PEN')
    line_extension.text = str(nota.op_gravada)

    tax_inclusive = etree.SubElement(legal_total, f'{{{CBC}}}TaxInclusiveAmount')
    tax_inclusive.set('currencyID', 'PEN')
    tax_inclusive.text = str(nota.importe)

    payable_amount = etree.SubElement(legal_total, f'{{{CBC}}}PayableAmount')
    payable_amount.set('currencyID', 'PEN')
    payable_amount.text = str(nota.importe)

    # CreditNoteLines
    for idx, detalle in enumerate(nota.detalles.all(), 1):
        credit_line = etree.SubElement(root, f'{{{CAC}}}CreditNoteLine')
        line_id = etree.SubElement(credit_line, f'{{{CBC}}}ID')
        line_id.text = str(idx)

        cred_quantity = etree.SubElement(credit_line, f'{{{CBC}}}CreditedQuantity')
        cred_quantity.set('unitCode', UNIDADES_MEDIDA.get(detalle.producto.unidad_medida, 'NIU'))
        cred_quantity.text = str(detalle.cantidad)

        line_extension_amount = etree.SubElement(credit_line, f'{{{CBC}}}LineExtensionAmount')
        line_extension_amount.set('currencyID', 'PEN')
        line_extension_amount.text = str(detalle.subtotal)

        pricing_ref = etree.SubElement(credit_line, f'{{{CAC}}}PricingReference')
        alt_price = etree.SubElement(pricing_ref, f'{{{CAC}}}AlternativeConditionPrice')
        alt_price_amount = etree.SubElement(alt_price, f'{{{CBC}}}PriceAmount')
        alt_price_amount.set('currencyID', 'PEN')
        alt_price_amount.text = str(float(detalle.precio_unitario) * 1.18)
        alt_price_type = etree.SubElement(alt_price, f'{{{CBC}}}PriceTypeCode')
        alt_price_type.set('listName', 'Tipo de Precio')
        alt_price_type.set('listAgencyName', 'PE:SUNAT')
        alt_price_type.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo16')
        alt_price_type.text = '01'

        line_tax = etree.SubElement(credit_line, f'{{{CAC}}}TaxTotal')
        line_tax_amount = etree.SubElement(line_tax, f'{{{CBC}}}TaxAmount')
        line_tax_amount.set('currencyID', 'PEN')
        line_tax_amount.text = str(detalle.igv_linea or '0.00')
        line_tax_subtotal = etree.SubElement(line_tax, f'{{{CAC}}}TaxSubtotal')
        line_tax_subtotal_base = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxableAmount')
        line_tax_subtotal_base.set('currencyID', 'PEN')
        line_tax_subtotal_base.text = str(detalle.subtotal)
        line_tax_subtotal_amount = etree.SubElement(line_tax_subtotal, f'{{{CBC}}}TaxAmount')
        line_tax_subtotal_amount.set('currencyID', 'PEN')
        line_tax_subtotal_amount.text = str(detalle.igv_linea or '0.00')
        line_tax_item = etree.SubElement(line_tax_subtotal, f'{{{CAC}}}TaxCategory')
        line_tax_item_id = etree.SubElement(line_tax_item, f'{{{CBC}}}ID')
        line_tax_item_id.text = 'S'
        line_tax_item_percent = etree.SubElement(line_tax_item, f'{{{CBC}}}Percent')
        line_tax_item_percent.text = '18.00'
        line_tax_exemption = etree.SubElement(line_tax_item, f'{{{CBC}}}TaxExemptionReasonCode')
        line_tax_exemption.set('listAgencyName', 'PE:SUNAT')
        line_tax_exemption.set('listName', 'Afectacion del IGV')
        line_tax_exemption.set('listURI', 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo07')
        line_tax_exemption.text = '10'
        line_tax_scheme = etree.SubElement(line_tax_item, f'{{{CAC}}}TaxScheme')
        line_tax_scheme_id = etree.SubElement(line_tax_scheme, f'{{{CBC}}}ID')
        line_tax_scheme_id.text = '1000'
        line_tax_scheme_name = etree.SubElement(line_tax_scheme, f'{{{CBC}}}Name')
        line_tax_scheme_name.text = 'IGV'
        line_tax_scheme_type = etree.SubElement(line_tax_scheme, f'{{{CBC}}}TaxTypeCode')
        line_tax_scheme_type.text = 'VAT'

        line_item = etree.SubElement(credit_line, f'{{{CAC}}}Item')
        line_description = etree.SubElement(line_item, f'{{{CBC}}}Description')
        line_description.text = detalle.producto.descripcion
        line_item_seller = etree.SubElement(line_item, f'{{{CAC}}}SellersItemIdentification')
        line_item_seller_id = etree.SubElement(line_item_seller, f'{{{CBC}}}ID')
        line_item_seller_id.text = getattr(detalle.producto, 'codigo', '001') or '001'

        price = etree.SubElement(credit_line, f'{{{CAC}}}Price')
        price_amount = etree.SubElement(price, f'{{{CBC}}}PriceAmount')
        price_amount.set('currencyID', 'PEN')
        price_amount.text = str(detalle.precio_unitario)

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