"""
Service Layer para el módulo de Clientes.
"""

from apps.clientes.models import Cliente
from apps.core.exceptions import ClienteNoEncontrado, DocumentoClienteInvalido


class ClienteService:
    """Lógica de negocio para gestión de clientes."""

    @staticmethod
    def crear(data: dict, usuario=None) -> Cliente:
        """Crea un nuevo cliente con validaciones de dominio."""
        cliente = Cliente(
            tipo_doc=data.get('tipo_doc', '6'),
            num_doc=data['num_doc'],
            razon_social=data['razon_social'],
            direccion=data.get('direccion', ''),
            telefono=data.get('telefono', ''),
            email=data.get('email', ''),
            ubigeo=data.get('ubigeo', ''),
            creado_por=usuario,
        )
        cliente.save()
        return cliente

    @staticmethod
    def actualizar(cliente_id: int, data: dict) -> Cliente:
        """Actualiza un cliente existente."""
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            raise ClienteNoEncontrado(f"No existe cliente con id={cliente_id}")

        for campo, valor in data.items():
            if hasattr(cliente, campo) and campo not in ('id', 'codigo', 'creado_en', 'creado_por'):
                setattr(cliente, campo, valor)
        cliente.save()
        return cliente

    @staticmethod
    def eliminar(cliente_id: int, usuario=None) -> None:
        """Soft delete de un cliente."""
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
        except Cliente.DoesNotExist:
            raise ClienteNoEncontrado(f"No existe cliente con id={cliente_id}")

        cliente.eliminar(usuario=usuario)
