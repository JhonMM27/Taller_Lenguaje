"""
Servicio de dominio: ProductoService.

Caso de uso: gestion de productos (CRUD + busqueda).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from ..entidades.producto import Producto
from ..excepciones import ProductoNoEncontrado
from ..puertos.repositorios import IProductoRepository


class ProductoService:
    def __init__(self, productos_repo: IProductoRepository) -> None:
        self._repo = productos_repo

    def crear(self, datos: dict) -> Producto:
        producto = Producto(
            id=None,
            descripcion=datos["descripcion"],
            precio_unitario=Decimal(str(datos["precio_unitario"])),
            unidad_medida=datos.get("unidad_medida", "NIU"),
            afecto_igv=datos.get("afecto_igv", True),
            cod_tipo_afectacion=datos.get("cod_tipo_afectacion", "10"),
            tipo_operacion=datos.get("tipo_operacion", "GRAVADA"),
            categoria_id=datos.get("categoria_id"),
        )
        return self._repo.guardar(producto)

    def obtener(self, producto_id: int) -> Producto:
        return self._repo.obtener_por_id(producto_id)

    def buscar(self, query: str = "", limit: int = 50) -> list[Producto]:
        return self._repo.buscar(query=query, limit=limit)

    def eliminar(self, producto_id: int, usuario_id: Optional[int] = None) -> None:
        try:
            self._repo.obtener_por_id(producto_id)
        except Exception as exc:
            raise ProductoNoEncontrado(
                f"No existe producto con id={producto_id}"
            ) from exc
        self._repo.eliminar_soft(producto_id, usuario_id)