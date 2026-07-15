"""
Service Layer para el módulo de Notas de Crédito.

Toda la lógica de negocio de emisión y validación de notas de crédito.
"""

from decimal import Decimal
from django.db import transaction
from django.conf import settings

from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
from apps.comprobantes.models import Comprobante
from apps.core.exceptions import (
    MontoExcedidoError,
    ComprobanteNoAceptado,
    ComprobanteNoEncontrado,
    RecursoNoEncontrado,
)


class NotaCreditoService:
    """Lógica de negocio para notas de crédito."""

    @staticmethod
    @transaction.atomic
    def emitir(data: dict, usuario=None) -> NotaCredito:
        """
        Emite una nota de crédito contra un comprobante existente.

        Args:
            data: dict con comprobante_id, tipo_nc, tipo_nota, descripcion, detalles
            usuario: User que crea la NC

        Returns:
            NotaCredito creada

        Raises:
            ComprobanteNoEncontrado, ComprobanteNoAceptado, MontoExcedidoError
        """
        try:
            comprobante = Comprobante.objects.get(id=data['comprobante_id'])
        except Comprobante.DoesNotExist:
            raise ComprobanteNoEncontrado(
                f"No existe comprobante con id={data['comprobante_id']}"
            )

        if comprobante.estado != 'ACEPTADO':
            raise ComprobanteNoAceptado(
                f"Solo se puede emitir NC contra comprobantes ACEPTADOS. "
                f"Estado actual del comprobante: {comprobante.estado}"
            )

        # Determinar serie de NC
        serie = 'FC01'
        if comprobante.serie:
            if comprobante.serie.tipo == '01':
                serie = 'FC' + comprobante.serie.serie[2:] if len(comprobante.serie.serie) >= 2 else 'FC01'
            elif comprobante.serie.tipo == '03':
                serie = 'FB' + comprobante.serie.serie[2:] if len(comprobante.serie.serie) >= 2 else 'FB01'

        notas_existentes = NotaCredito.objects.filter(serie=serie).count()
        numero = notas_existentes + 1

        # Validar monto si se proporcionan detalles
        detalles_data = data.get('detalles', [])
        monto_afectado = Decimal(str(data.get('monto_afectado', 0)))

        if monto_afectado > comprobante.total:
            raise MontoExcedidoError(
                f"El monto afectado (S/ {monto_afectado}) excede el total del "
                f"comprobante original (S/ {comprobante.total})."
            )

        nota = NotaCredito.objects.create(
            comprobante_referencia=comprobante,
            serie=serie,
            numero=numero,
            tipo_nc=data.get('tipo_nc', 'NC'),
            tipo_nota=data.get('tipo_nota', '01'),
            descripcion=data.get('descripcion', ''),
            estado='BORRADOR',
            creado_por=usuario,
        )

        # Crear detalles si se proporcionan
        if detalles_data:
            tasa_igv = Decimal(str(settings.IGV_TASA))
            for det in detalles_data:
                from apps.productos.models import Producto
                producto = Producto.objects.get(id=det['producto_id'])
                cantidad = Decimal(str(det['cantidad']))
                precio_unitario = Decimal(str(det['precio_unitario']))
                base = cantidad * precio_unitario
                igv_linea = round(base * tasa_igv, 2) if det.get('afecto_igv', True) else Decimal('0.00')

                DetalleNotaCredito.objects.create(
                    nota_credito=nota,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    afecto_igv=det.get('afecto_igv', True),
                    igv_linea=igv_linea,
                    subtotal=base,
                    creado_por=usuario,
                )

            nota.calcular_totales()

        return nota

    @staticmethod
    def eliminar(nota_id: int, usuario=None) -> None:
        """
        Soft delete de una nota de crédito.

        Raises:
            RecursoNoEncontrado
        """
        try:
            nota = NotaCredito.objects.get(pk=nota_id)
        except NotaCredito.DoesNotExist:
            raise RecursoNoEncontrado(
                f"No existe nota de crédito con id={nota_id}"
            )

        nota.eliminar(usuario=usuario)
