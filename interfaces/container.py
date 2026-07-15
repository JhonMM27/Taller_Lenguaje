"""
Container de dependencias.

Aqui se hace el wiring de todos los servicios del dominio con sus
adaptadores de infraestructura. Esto es el unico punto donde el dominio
conoce la infraestructura concreta.
"""
from __future__ import annotations

from dominio.event_bus import event_bus
from dominio.servicios import (
    ClienteService,
    ComprobanteService,
    NotaCreditoService,
    ProductoService,
)
from infraestructura.persistencia import (
    DjangoClienteRepository,
    DjangoProductoRepository,
    DjangoUnitOfWork,
)


def get_uow() -> DjangoUnitOfWork:
    """Retorna una nueva instancia de UoW.

    La UoW no mantiene estado entre llamadas, los servicios
    la usan dentro de un `with uow:` que controla la transaccion.
    """
    return DjangoUnitOfWork()


def reset_uow() -> None:
    """No-op: las UoW son por-llamada, no hay estado a resetear."""
    pass


def get_comprobante_service() -> ComprobanteService:
    return ComprobanteService(
        uow=get_uow(),
        event_bus=event_bus,
    )


def get_nota_credito_service() -> NotaCreditoService:
    return NotaCreditoService(
        uow=get_uow(),
        event_bus=event_bus,
    )


def get_cliente_service() -> ClienteService:
    return ClienteService(clientes_repo=DjangoClienteRepository())


def get_producto_service() -> ProductoService:
    return ProductoService(productos_repo=DjangoProductoRepository())


def get_sunat_service():
    from infraestructura.sunat.factory import get_sunat_envio_service
    return get_sunat_envio_service(get_uow())