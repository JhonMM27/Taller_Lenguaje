"""
Contratos (Protocol) de los repositorios que el dominio necesita.

Estos Protocols definen la API minima esperada por los servicios del dominio.
Los adaptadores en `infraestructura/persistencia/` los implementan usando
Django ORM, pero el dominio NO sabe nada de eso.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol, runtime_checkable

from ..entidades import (
    Comprobante,
    DetalleComprobante,
    NotaCredito,
    DetalleNotaCredito,
    SerieComprobante,
    Cliente,
    Producto,
    Empresa,
)


# ============================================================
# Repositorios principales
# ============================================================

@runtime_checkable
class IComprobanteRepository(Protocol):
    """Contrato para persistencia de comprobantes."""

    def obtener_por_id(self, comprobante_id: int) -> Comprobante:
        """Retorna un comprobante por su id. Lanza ComprobanteNoEncontrado."""
        ...

    def listar(
        self,
        empresa_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        tipo: str = "",
        estado: str = "",
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        ruc_cliente: str = "",
        solo_activos: bool = True,
    ) -> list[Comprobante]:
        ...

    def guardar(self, comprobante: Comprobante) -> Comprobante:
        ...

    def eliminar_soft(self, comprobante_id: int, usuario_id: Optional[int] = None) -> None:
        ...

    def existe_serie_numero(self, serie_id: int, numero: int) -> bool:
        ...


@runtime_checkable
class INotaCreditoRepository(Protocol):
    """Contrato para persistencia de notas de credito."""

    def obtener_por_id(self, nota_id: int) -> NotaCredito:
        ...

    def listar(
        self,
        empresa_id: Optional[int] = None,
        estado: str = "",
        solo_activos: bool = True,
    ) -> list[NotaCredito]:
        ...

    def guardar(self, nota: NotaCredito) -> NotaCredito:
        ...

    def eliminar_soft(self, nota_id: int, usuario_id: Optional[int] = None) -> None:
        ...

    def siguiente_numero(self, serie: str) -> int:
        ...


@runtime_checkable
class ISerieComprobanteRepository(Protocol):
    """Contrato para la gestion de series y numeracion."""

    def obtener_o_crear(
        self, empresa_id: int, tipo: str
    ) -> tuple[SerieComprobante, bool]:
        """Obtiene o crea una serie para (empresa, tipo)."""
        ...

    def siguiente_correlativo(
        self, empresa_id: int, tipo: str
    ) -> tuple[SerieComprobante, int]:
        """Devuelve la serie y el siguiente numero correlativo.

        Implementacion: usar un mecanismo atomico (SELECT FOR UPDATE en BD)
        para garantizar correlativos sin saltos.
        """
        ...

    def guardar(self, serie: SerieComprobante) -> None:
        ...


@runtime_checkable
class IClienteRepository(Protocol):
    """Contrato para persistencia de clientes."""

    def obtener_por_id(self, cliente_id: int) -> Cliente:
        ...

    def buscar(
        self, query: str = "", solo_activos: bool = True, limit: int = 50
    ) -> list[Cliente]:
        ...

    def guardar(self, cliente: Cliente) -> Cliente:
        ...

    def eliminar_soft(self, cliente_id: int, usuario_id: Optional[int] = None) -> None:
        ...


@runtime_checkable
class IProductoRepository(Protocol):
    """Contrato para persistencia de productos."""

    def obtener_por_id(self, producto_id: int) -> Producto:
        ...

    def buscar(
        self, query: str = "", solo_activos: bool = True, limit: int = 50
    ) -> list[Producto]:
        ...

    def guardar(self, producto: Producto) -> Producto:
        ...

    def eliminar_soft(self, producto_id: int, usuario_id: Optional[int] = None) -> None:
        ...


@runtime_checkable
class IEmpresaRepository(Protocol):
    """Contrato para persistencia de empresas."""

    def obtener_por_id(self, empresa_id: int) -> Empresa:
        ...

    def listar(self, solo_activos: bool = True) -> list[Empresa]:
        ...

    def guardar(self, empresa: Empresa) -> Empresa:
        ...

    def eliminar_soft(self, empresa_id: int, usuario_id: Optional[int] = None) -> None:
        ...


@runtime_checkable
class ILogSunatRepository(Protocol):
    """Contrato para persistencia del log de envios a SUNAT."""

    def registrar(
        self,
        comprobante: Comprobante,
        estado_respuesta: str,
        codigo_respuesta: str,
        descripcion: str,
        uuid: str = "",
        cdr_xml: str = "",
    ) -> None:
        ...

    def obtener_por_comprobante(self, comprobante_id: int) -> list:
        ...


# ============================================================
# Unit of Work (transacciones)
# ============================================================

@runtime_checkable
class IUnitOfWork(Protocol):
    """Abstraccion de una unidad de trabajo transaccional."""

    def __enter__(self) -> "IUnitOfWork":
        ...

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    @property
    def comprobantes(self) -> IComprobanteRepository:
        ...

    @property
    def notas_credito(self) -> INotaCreditoRepository:
        ...

    @property
    def series(self) -> ISerieComprobanteRepository:
        ...

    @property
    def clientes(self) -> IClienteRepository:
        ...

    @property
    def productos(self) -> IProductoRepository:
        ...

    @property
    def empresas(self) -> IEmpresaRepository:
        ...

    @property
    def logs_sunat(self) -> ILogSunatRepository:
        ...