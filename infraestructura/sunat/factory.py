"""
Factory para obtener instancias de servicios SUNAT segun configuracion.

Permite alternar entre mock y real desde settings sin que el dominio
se entere.
"""
from __future__ import annotations

import os

from dominio.puertos.repositorios import IUnitOfWork
from dominio.puertos.sunat import IOSEService, IXmlSigner
from dominio.servicios import SunatEnvioService

from .mock_ose import MockOSEAdapter
from .real_ose import RealOSEAdapter
from .signer_adapter import XmlSignerAdapter
from .xml_generator_adapter import XmlGeneratorAdapter
from .zip_helper import zip_nombre_comprobante, crear_zip


def get_ose_client() -> IOSEService:
    """Retorna el cliente OSE segun SUNAT_OSE_MOCK."""
    es_mock = os.getenv("SUNAT_OSE_MOCK", "True") == "True"
    if es_mock:
        return MockOSEAdapter()
    return RealOSEAdapter(
        wsdl_url=os.getenv("SUNAT_OSE_WSDL", ""),
        usuario=os.getenv("SUNAT_OSE_USUARIO", ""),
        password=os.getenv("SUNAT_OSE_PASSWORD", ""),
        ruc=os.getenv("SUNAT_OSE_RUC", ""),
    )


def get_signer() -> IXmlSigner:
    return XmlSignerAdapter()


def get_xml_generator() -> XmlGeneratorAdapter:
    return XmlGeneratorAdapter()


def get_sunat_envio_service(uow: IUnitOfWork) -> SunatEnvioService:
    """Wiring del SunatEnvioService con todos sus colaboradores."""
    return SunatEnvioService(
        uow=uow,
        ose=get_ose_client(),
        signer=get_signer(),
        xml_generator=get_xml_generator(),
        zip_nombre_fn=zip_nombre_comprobante,
        zip_crear_fn=crear_zip,
    )