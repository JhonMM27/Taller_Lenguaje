"""
Service Layer para el módulo de Productos.
"""

from apps.productos.models import Producto, CategoriaProducto
from apps.core.exceptions import ProductoNoEncontrado


class ProductoService:
    """Lógica de negocio para gestión de productos."""

    @staticmethod
    def crear(data: dict, usuario=None) -> Producto:
        """Crea un nuevo producto con validaciones de dominio."""
        categoria = None
        if data.get('categoria_id'):
            categoria = CategoriaProducto.objects.filter(id=data['categoria_id']).first()

        producto = Producto(
            descripcion=data['descripcion'],
            unidad_medida=data.get('unidad_medida', 'NIU'),
            precio_unitario=data['precio_unitario'],
            afecto_igv=data.get('afecto_igv', True),
            cod_tipo_afectacion=data.get('cod_tipo_afectacion', '10'),
            categoria=categoria,
            tipo_operacion=data.get('tipo_operacion', 'GRAVADA'),
            creado_por=usuario,
        )
        producto.save()
        return producto

    @staticmethod
    def actualizar(producto_id: int, data: dict) -> Producto:
        """Actualiza un producto existente."""
        try:
            producto = Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist:
            raise ProductoNoEncontrado(f"No existe producto con id={producto_id}")

        for campo, valor in data.items():
            if hasattr(producto, campo) and campo not in ('id', 'codigo', 'creado_en', 'creado_por'):
                setattr(producto, campo, valor)
        producto.save()
        return producto

    @staticmethod
    def eliminar(producto_id: int, usuario=None) -> None:
        """Soft delete de un producto."""
        try:
            producto = Producto.objects.get(pk=producto_id)
        except Producto.DoesNotExist:
            raise ProductoNoEncontrado(f"No existe producto con id={producto_id}")

        producto.eliminar(usuario=usuario)
