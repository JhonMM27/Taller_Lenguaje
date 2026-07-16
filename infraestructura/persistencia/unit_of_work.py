"""
Unit of Work concreto basado en Django ORM.

Implementa IUnitOfWork del dominio. Maneja transacciones con
`transaction.atomic()`. Todos los repositorios comparten la misma
transaccion dentro de un bloque `with`.
"""
from __future__ import annotations

from django.db import transaction

from dominio.puertos.repositorios import IUnitOfWork

from .repos import (
    DjangoComprobanteRepository,
    DjangoNotaCreditoRepository,
    DjangoSerieComprobanteRepository,
    DjangoClienteRepository,
    DjangoProductoRepository,
    DjangoEmpresaRepository,
    DjangoLogSunatRepository,
)


class DjangoUnitOfWork(IUnitOfWork):
    """Unit of Work transaccional sobre Django ORM."""

    def __init__(self) -> None:
        self._comprobantes = DjangoComprobanteRepository()
        self._notas_credito = DjangoNotaCreditoRepository()
        self._series = DjangoSerieComprobanteRepository()
        self._clientes = DjangoClienteRepository()
        self._productos = DjangoProductoRepository()
        self._empresas = DjangoEmpresaRepository()
        self._logs_sunat = DjangoLogSunatRepository()
        self._tx = None

    def __enter__(self) -> "DjangoUnitOfWork":
        self._tx = transaction.atomic()
        self._tx.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._tx is not None:
            self._tx.__exit__(exc_type, exc_val, exc_tb)
            self._tx = None

    def commit(self) -> None:
        if self._tx is not None:
            # transaction.atomic commitea al salir del with sin excepcion.
            # Aqui podemos forzar savepoint flush.
            pass

    def rollback(self) -> None:
        # transaction.atomic hace rollback automatico si hay excepcion.
        # Aqui solo limpiamos el wrapper.
        self._tx = None

    @property
    def comprobantes(self) -> DjangoComprobanteRepository:
        return self._comprobantes

    @property
    def notas_credito(self) -> DjangoNotaCreditoRepository:
        return self._notas_credito

    @property
    def series(self) -> DjangoSerieComprobanteRepository:
        return self._series

    @property
    def clientes(self) -> DjangoClienteRepository:
        return self._clientes

    @property
    def productos(self) -> DjangoProductoRepository:
        return self._productos

    @property
    def empresas(self) -> DjangoEmpresaRepository:
        return self._empresas

    @property
    def logs_sunat(self) -> DjangoLogSunatRepository:
        return self._logs_sunat