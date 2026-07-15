"""Adaptadores de persistencia (Django ORM)."""
from .mappers import (
    empresa_a_modelo,
    modelo_a_empresa,
    cliente_a_modelo,
    modelo_a_cliente,
    producto_a_modelo,
    modelo_a_producto,
    comprobante_a_modelo,
    modelo_a_comprobante,
    nota_credito_a_modelo,
    modelo_a_nota_credito,
    detalle_comprobante_a_modelo,
    modelo_a_detalle_comprobante,
    detalle_nota_credito_a_modelo,
    modelo_a_detalle_nota_credito,
    serie_a_modelo,
    modelo_a_serie,
)
from .unit_of_work import DjangoUnitOfWork
from .repos import (
    DjangoComprobanteRepository,
    DjangoNotaCreditoRepository,
    DjangoSerieComprobanteRepository,
    DjangoClienteRepository,
    DjangoProductoRepository,
    DjangoEmpresaRepository,
    DjangoLogSunatRepository,
)

__all__ = [
    "DjangoUnitOfWork",
    "DjangoComprobanteRepository",
    "DjangoNotaCreditoRepository",
    "DjangoSerieComprobanteRepository",
    "DjangoClienteRepository",
    "DjangoProductoRepository",
    "DjangoEmpresaRepository",
    "DjangoLogSunatRepository",
]