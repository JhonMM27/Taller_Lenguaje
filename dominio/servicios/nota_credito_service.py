"""
Servicio de dominio: NotaCreditoService.

Caso de uso: emitir notas de credito contra comprobantes ACEPTADOS.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from ..entidades.nota_credito import (
    NotaCredito,
    DetalleNotaCredito,
)
from ..eventos import (
    NotaCreditoEmitida,
    NotaCreditoAceptada,
    NotaCreditoRechazada,
)
from ..excepciones import (
    ComprobanteNoEncontrado,
    NotaCreditoNoEncontrada,
    ProductoNoEncontrado,
    RecursoNoEncontrado,
)
from ..puertos.repositorios import (
    IComprobanteRepository,
    INotaCreditoRepository,
    IProductoRepository,
    IUnitOfWork,
)


class _EventBus(Protocol):
    def publish(self, event) -> None: ...


class NotaCreditoService:
    """Caso de uso: gestion de notas de credito."""

    def __init__(
        self,
        uow: IUnitOfWork,
        event_bus: Optional[_EventBus] = None,
        tasa_igv: Decimal = Decimal("0.18"),
    ) -> None:
        self._uow = uow
        self._events = event_bus
        self._tasa_igv = Decimal(str(tasa_igv))

    def emitir(
        self,
        comprobante_referencia_id: int,
        tipo_nc: str,
        tipo_nota: str,
        descripcion: str,
        detalles_data: Optional[list[dict]] = None,
        creado_por_id: Optional[int] = None,
        monto_afectado: Optional[Decimal] = None,
    ) -> NotaCredito:
        """
        Emite una NC contra un comprobante existente.

        Validaciones:
            - El comprobante debe estar ACEPTADO.
            - El monto total no debe exceder el del comprobante original.

        Si `monto_afectado` viene dado, se usa como importe directo
        (sin detalles). Si no, se calcula desde los detalles.
        """
        try:
            comprobante = self._uow.comprobantes.obtener_por_id(
                comprobante_referencia_id
            )
        except Exception as exc:
            raise ComprobanteNoEncontrado(
                f"No existe comprobante con id={comprobante_referencia_id}"
            ) from exc

        # Determinar serie de la NC segun tipo del comprobante
        serie = self._calcular_serie(comprobante.tipo)
        numero = self._uow.notas_credito.siguiente_numero(serie)

        detalles = []
        for d in (detalles_data or []):
            try:
                producto = self._uow.productos.obtener_por_id(d["producto_id"])
            except Exception as exc:
                raise ProductoNoEncontrado(
                    f"No existe producto con id={d['producto_id']}"
                ) from exc

            cantidad = Decimal(str(d.get("cantidad", 1)))
            precio = Decimal(str(d.get("precio_unitario", producto.precio_unitario)))
            detalles.append(DetalleNotaCredito(
                id=None,
                nota_credito_id=0,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento=Decimal(str(d.get("descuento", 0))),
                afecto_igv=producto.afecto_igv,
                cod_tipo_afectacion=producto.cod_tipo_afectacion,
            ))

        nota = NotaCredito(
            id=None,
            comprobante_referencia_id=comprobante.id,
            serie=serie,
            numero=numero,
            fecha=date.today(),
            tipo_nc=tipo_nc,
            tipo_nota=tipo_nota,
            descripcion=descripcion,
            detalles=detalles,
        )

        # Validar primero contra comprobante (debe estar ACEPTADO)
        nota.validar_contra_comprobante(comprobante)

        # Si hay monto_afectado explicito, usarlo; si no, calcular de detalles
        if monto_afectado is not None:
            nota.importe = Decimal(str(monto_afectado))
            # Aproximacion: IGV incluido
            nota.igv = (nota.importe / Decimal("1.18")).quantize(Decimal("0.01"))
            nota.op_gravada = nota.importe - nota.igv
        else:
            nota.calcular_totales(self._tasa_igv)

        # Validar que el monto no exceda al comprobante
        nota.validar_monto(comprobante)

        with self._uow:
            guardada = self._uow.notas_credito.guardar(nota)
            self._uow.commit()

        if self._events is not None:
            self._events.publish(NotaCreditoEmitida(
                nota_id=guardada.id,
                comprobante_referencia_id=comprobante.id,
                importe=guardada.importe,
            ))
        return guardada

    def eliminar(
        self,
        nota_id: int,
        usuario_id: Optional[int] = None,
    ) -> None:
        try:
            self._uow.notas_credito.obtener_por_id(nota_id)
        except Exception as exc:
            raise NotaCreditoNoEncontrada(
                f"No existe NC con id={nota_id}"
            ) from exc
        with self._uow:
            self._uow.notas_credito.eliminar_soft(nota_id, usuario_id)
            self._uow.commit()

    def marcar_aceptada(
        self, nota_id: int, ticket: Optional[str] = None
    ) -> NotaCredito:
        nota = self._uow.notas_credito.obtener_por_id(nota_id)
        nota.estado = "ACEPTADO"
        nota.sunat_ticket = ticket
        with self._uow:
            guardada = self._uow.notas_credito.guardar(nota)
            self._uow.commit()
        if self._events is not None:
            self._events.publish(NotaCreditoAceptada(
                nota_id=guardada.id, ticket=ticket
            ))
        return guardada

    def marcar_rechazada(
        self, nota_id: int, motivo: str
    ) -> NotaCredito:
        nota = self._uow.notas_credito.obtener_por_id(nota_id)
        nota.estado = "RECHAZADO"
        nota.mensaje_sunat = motivo
        with self._uow:
            guardada = self._uow.notas_credito.guardar(nota)
            self._uow.commit()
        if self._events is not None:
            self._events.publish(NotaCreditoRechazada(
                nota_id=guardada.id, motivo=motivo
            ))
        return guardada

    @staticmethod
    def _calcular_serie(tipo_comprobante: str) -> str:
        if tipo_comprobante == "01":
            return "FC01"
        if tipo_comprobante == "03":
            return "FB01"
        return "FC01"