"""
Servicio de dominio: ClienteService.

Caso de uso: gestion de clientes (CRUD + busqueda).
"""
from __future__ import annotations

from typing import Optional

from ..entidades.cliente import Cliente
from ..excepciones import ClienteNoEncontrado, RecursoNoEncontrado
from ..puertos.repositorios import IClienteRepository


class ClienteService:
    def __init__(self, clientes_repo: IClienteRepository) -> None:
        self._repo = clientes_repo

    def crear(self, datos: dict) -> Cliente:
        cliente = Cliente(
            id=None,
            tipo_doc=datos["tipo_doc"],
            num_doc=datos["num_doc"],
            razon_social=datos["razon_social"],
            codigo=datos.get("codigo"),
            direccion=datos.get("direccion"),
            telefono=datos.get("telefono"),
            email=datos.get("email"),
            ubigeo=datos.get("ubigeo"),
            pais_codigo=datos.get("pais_codigo", "PE"),
        )
        return self._repo.guardar(cliente)

    def obtener(self, cliente_id: int) -> Cliente:
        return self._repo.obtener_por_id(cliente_id)

    def buscar(self, query: str = "", limit: int = 50) -> list[Cliente]:
        return self._repo.buscar(query=query, limit=limit)

    def eliminar(self, cliente_id: int, usuario_id: Optional[int] = None) -> None:
        try:
            self._repo.obtener_por_id(cliente_id)
        except Exception as exc:
            raise ClienteNoEncontrado(
                f"No existe cliente con id={cliente_id}"
            ) from exc
        self._repo.eliminar_soft(cliente_id, usuario_id)
