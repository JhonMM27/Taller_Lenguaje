"""
Puertos del dominio (interfaces / contratos).

Define los contratos que el dominio espera de sus colaboradores externos
(repositorios, servicios externos). Los adaptadores en `infraestructura/`
implementan estos Protocols.
"""
from .repositorios import (
    IComprobanteRepository,
    INotaCreditoRepository,
    ISerieComprobanteRepository,
    IClienteRepository,
    IProductoRepository,
    IEmpresaRepository,
    ILogSunatRepository,
    IUnitOfWork,
)
from .sunat import IOSEService, IXmlSigner

__all__ = [
    "IComprobanteRepository",
    "INotaCreditoRepository",
    "ISerieComprobanteRepository",
    "IClienteRepository",
    "IProductoRepository",
    "IEmpresaRepository",
    "ILogSunatRepository",
    "IUnitOfWork",
    "IOSEService",
    "IXmlSigner",
]