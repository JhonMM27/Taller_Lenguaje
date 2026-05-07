import logging
import os
import base64
import hashlib
from lxml import etree
from django.conf import settings

logger = logging.getLogger(__name__)

NAMESPACES_FIRMA = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'inv': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
}

DS = NAMESPACES_FIRMA['ds']
EXT = NAMESPACES_FIRMA['ext']


def get_cert_bytes(cert_path=None, cert_password=None):
    cert_path = cert_path or os.getenv('SUNAT_CERT_PATH', '/media/CT2602141470.pfx')
    cert_password = cert_password or os.getenv('SUNAT_CERT_PASSWORD', 'Lavagna2026')

    if not os.path.exists(cert_path):
        raise FileNotFoundError(f"Certificado no encontrado: {cert_path}")

    with open(cert_path, 'rb') as f:
        return f.read()


def sign_xml(xml_content, ruc=None, razon_social=None):
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.hazmat.primitives.asymmetric import padding

    root = etree.fromstring(xml_content)

    cert_path = os.getenv('SUNAT_CERT_PATH', '/media/CT2602141470.pfx')
    cert_password = os.getenv('SUNAT_CERT_PASSWORD', 'Lavagna2026')

    cert_data = get_cert_bytes(cert_path, cert_password)
    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        cert_data,
        cert_password.encode('utf-8')
    )

    ruc = ruc or '20103129061'
    razon_social = razon_social or 'MI EMPRESA SAC'

    ext_UBLExtensions = root.find(f'{{{EXT}}}UBLExtensions')
    if ext_UBLExtensions is None:
        raise ValueError("No se encontro UBLExtensions en el XML")

    for ext_extension in ext_UBLExtensions.findall(f'{{{EXT}}}UBLExtension'):
        ext_content = ext_extension.find(f'{{{EXT}}}ExtensionContent')
        if ext_content is not None:
            for sig in ext_content.findall(f'{{{DS}}}Signature'):
                ext_content.remove(sig)

            ds_sig = etree.SubElement(ext_content, f'{{{DS}}}Signature')
            ds_sig.set('Id', 'SignatureSUNAT')

            ds_signed_info = etree.SubElement(ds_sig, f'{{{DS}}}SignedInfo')

            ds_canonicalization_method = etree.SubElement(ds_signed_info, f'{{{DS}}}CanonicalizationMethod')
            ds_canonicalization_method.set('Algorithm', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315')

            ds_signature_method = etree.SubElement(ds_signed_info, f'{{{DS}}}SignatureMethod')
            ds_signature_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1')

            ds_reference = etree.SubElement(ds_signed_info, f'{{{DS}}}Reference')
            ds_reference.set('URI', '')

            ds_digest_method = etree.SubElement(ds_reference, f'{{{DS}}}DigestMethod')
            ds_digest_method.set('Algorithm', 'http://www.w3.org/2000/09/xmldsig#sha1')

            ds_digest_value = etree.SubElement(ds_reference, f'{{{DS}}}DigestValue')

            ds_signature_value = etree.SubElement(ds_sig, f'{{{DS}}}SignatureValue')

            ds_key_info = etree.SubElement(ds_sig, f'{{{DS}}}KeyInfo')
            ds_x509_data = etree.SubElement(ds_key_info, f'{{{DS}}}X509Data')
            ds_x509_cert = etree.SubElement(ds_x509_data, f'{{{DS}}}X509Certificate')

            break

    canonical_root = etree.tostring(root, method='c14n')

    digest = hashlib.sha1(canonical_root).digest()
    digest_b64 = base64.b64encode(digest).decode('ascii')
    ds_digest_value.text = digest_b64

    canonical_signed_info = etree.tostring(ds_signed_info, method='c14n')

    signature_bytes = private_key.sign(
        canonical_signed_info,
        padding.PKCS1v15(),
        hashes.SHA1()
    )
    signature_b64 = base64.b64encode(signature_bytes).decode('ascii')
    ds_signature_value.text = signature_b64

    cert_der = certificate.public_bytes(serialization.Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode('ascii')
    ds_x509_cert.text = cert_b64

    return etree.tostring(root, xml_declaration=True, encoding='UTF-8')