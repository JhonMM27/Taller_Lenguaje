"""
Entidades de dominio: NotaCredito y DetalleNotaCredito.

Dataclasses Python puros. CERO dependencias de Django.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ..tributos import datos_afectacion_igv

from ..excepciones import (
    ComprobanteNoAceptado,
    EstadoInvalido,
    MontoExcedidoError,
    ReglaNegocioViolada,
)
from .comprobante import (
    ESTADO_ACEPTADO,
    ESTADO_BORRADOR,
    Comprobante,
)


# Motivos de NC segun SUNAT
MOTIVOS_NC = {
    "01": "Anulacion de la operacion",
    "06": "Devolucion por item",
    "07": "Devolucion total",
}

MOTIVOS_NCD = {
    "04": "Descuento global",
    "05": "Descuento por item",
    "08": "Bonificacion",
}


@dataclass
class DetalleNotaCredito:
    id: Optional[int]
    nota_credito_id: int
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")
    afecto_igv: bool = True
    cod_tipo_afectacion: str = "10"
    igv_linea: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ReglaNegocioViolada(
                "La cantidad debe ser mayor a cero"
            )

    def calcular_subtotal(self, tasa_igv: Decimal) -> Decimal:
        base = (self.precio_unitario - self.descuento) * self.cantidad
        datos_tributo = datos_afectacion_igv(self.cod_tipo_afectacion)
        if datos_tributo["gratuito"]:
            self.subtotal = Decimal("0.00")
            self.igv_linea = Decimal("0.00")
            return self.subtotal

        self.subtotal = base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tasa = datos_tributo["tasa"] / Decimal("100")
        if tasa:
            self.igv_linea = (base * tasa).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            self.igv_linea = Decimal("0.00")
        return self.subtotal

    @property
    def total_linea(self) -> Decimal:
        return self.subtotal + self.igv_linea


@dataclass
class NotaCredito:
    id: Optional[int]
    comprobante_referencia_id: int
    serie: str
    numero: int
    fecha: object
    tipo_nc: str = "NC"
    tipo_nota: str = "01"
    op_gravada: Decimal = Decimal("0")
    igv: Decimal = Decimal("0")
    importe: Decimal = Decimal("0")
    descripcion: str = ""
    estado: str = ESTADO_BORRADOR
    xml_firmado: Optional[str] = None
    sunat_ticket: Optional[str] = None
    cdr_xml: Optional[str] = None
    mensaje_sunat: Optional[str] = None
    detalles: list = field(default_factory=list)
    activo: bool = True

    def __post_init__(self) -> None:
        if not self.serie:
            raise ReglaNegocioViolada("La serie de la NC es obligatoria")
        if self.numero <= 0:
            raise ReglaNegocioViolada(
                "El numero de la NC debe ser positivo"
            )

    def validar_contra_comprobante(self, comprobante: Comprobante) -> None:
        """
        Regla de negocio: la NC solo puede emitirse contra comprobantes
        ACEPTADOS, y el importe no puede exceder el total.
        """
        if not isinstance(comprobante, Comprobante):
            raise ReglaNegocioViolada(
                "La referencia debe ser un comprobante"
            )
        if comprobante.estado != ESTADO_ACEPTADO:
            raise ComprobanteNoAceptado(
                f"Solo se puede emitir NC contra comprobantes ACEPTADOS. "
                f"Estado actual: {comprobante.estado}"
            )

    def validar_monto(self, comprobante: Comprobante) -> None:
        """El importe total de la NC no puede exceder el del comprobante."""
        if self.importe > comprobante.total:
            raise MontoExcedidoError(
                f"El importe de la NC (S/ {self.importe}) excede el total "
                f"del comprobante original (S/ {comprobante.total})."
            )

    def calcular_totales(self, tasa_igv: Decimal) -> None:
        """Calcula op_gravada, IGV e importe de la NC."""
        gravada = Decimal("0")
        igv = Decimal("0")
        for det in self.detalles:
            det.calcular_subtotal(tasa_igv)
            gravada += det.subtotal
            igv += det.igv_linea
        self.op_gravada = gravada.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.igv = igv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.importe = (self.op_gravada + self.igv).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def motivo_texto(self) -> str:
        if self.tipo_nc == "NC":
            return MOTIVOS_NC.get(self.tipo_nota, "")
        return MOTIVOS_NCD.get(self.tipo_nota, "")

    @property
    def numero_formateado(self) -> str:
        return f"{self.numero:08d}"
