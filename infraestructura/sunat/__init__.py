"""Adaptadores de SUNAT/OSE (cliente SOAP)."""
from .mock_ose import MockOSEAdapter
from .real_ose import RealOSEAdapter
from .signer_adapter import XmlSignerAdapter
from .xml_generator_adapter import XmlGeneratorAdapter
from .zip_helper import zip_nombre_comprobante, crear_zip
from .factory import get_ose_client, get_sunat_envio_service

__all__ = [
    "MockOSEAdapter",
    "RealOSEAdapter",
    "XmlSignerAdapter",
    "XmlGeneratorAdapter",
    "zip_nombre_comprobante",
    "crear_zip",
    "get_ose_client",
    "get_sunat_envio_service",
]