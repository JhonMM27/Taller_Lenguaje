"""
Entidades de dominio: Comprobante, DetalleComprobante y SerieComprobante.

Dataclasses Python puros. CERO dependencias de Django.
Contienen TODA la logica de negocio del comprobante electronico.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from ..excepciones import EstadoInvalido, ReglaNegocioViolada


# Tipos de comprobante electronico (SUNAT)
TIPO_FACTURA = "01"
TIPO_BOLETA = "03"
TIPO_NOTA_CREDITO = "07"
TIPO_NOTA_DEBITO = "08"

TIPOS_VALIDOS = (TIPO_FACTURA, TIPO_BOLETA, TIPO_NOTA_CREDITO, TIPO_NOTA_DEBITO)


# Estados del comprobante
ESTADO_BORRADOR = "BORRADOR"
ESTADO_EMITIDO = "EMITIDO"
ESTADO_ENVIADO = "ENVIADO"
ESTADO_ACEPTADO = "ACEPTADO"
ESTADO_RECHAZADO = "RECHAZADO"
ESTADO_ANULADO_PARCIAL = "ANULADO_PARCIAL"
ESTADO_ANULADO_TOTAL = "ANULADO_TOTAL"

ESTADOS_VALIDOS = (
    ESTADO_BORRADOR, ESTADO_EMITIDO, ESTADO_ENVIADO,
    ESTADO_ACEPTADO, ESTADO_RECHAZADO,
    ESTADO_ANULADO_PARCIAL, ESTADO_ANULADO_TOTAL,
)


@dataclass
class SerieComprobante:
    id: Optional[int]
    empresa_id: int
    tipo: str
    serie: str
    correlativo_actual: int = 0
    activo: bool = True

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_VALIDOS:
            raise ReglaNegocioViolada(
                f"Tipo de comprobante invalido: {self.tipo}"
            )

    @property
    def siguiente_correlativo(self) -> int:
        return self.correlativo_actual + 1

    def reservar_siguiente(self) -> int:
        """Avanza el correlativo y devuelve el numero asignado."""
        siguiente = self.siguiente_correlativo
        self.correlativo_actual = siguiente
        return siguiente


@dataclass
class DetalleComprobante:
    id: Optional[int]
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal = Decimal("0")
    afecto_igv: bool = True
    cod_tipo_afectacion: str = "10"
    igv_linea: Decimal = Decimal("0")
    subtotal: Decimal = Decimal("0")
    unidad_medida: str = "NIU"
    descripcion: str = ""
    codigo_producto: str = ""

    def __post_init__(self) -> None:
        if self.cantidad <= 0:
            raise ReglaNegocioViolada(
                "La cantidad debe ser mayor a cero"
            )
        if self.precio_unitario < 0:
            raise ReglaNegocioViolada(
                "El precio unitario no puede ser negativo"
            )

    def calcular_subtotal(self, tasa_igv: Decimal) -> Decimal:
        """Calcula subtotal e IGV del detalle."""
        base = (self.precio_unitario - self.descuento) * self.cantidad
        self.subtotal = base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if self.afecto_igv:
            self.igv_linea = (base * tasa_igv).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        else:
            self.igv_linea = Decimal("0.00")
        return self.subtotal

    @property
    def total_linea(self) -> Decimal:
        return self.subtotal + self.igv_linea


# Transiciones validas del estado del comprobante
TRANSICIONES_VALIDAS = {
    ESTADO_BORRADOR: [ESTADO_EMITIDO],
    ESTADO_EMITIDO: [ESTADO_ENVIADO, ESTADO_BORRADOR],
    ESTADO_ENVIADO: [ESTADO_ACEPTADO, ESTADO_RECHAZADO],
    ESTADO_RECHAZADO: [ESTADO_ENVIADO],
    ESTADO_ACEPTADO: [ESTADO_ANULADO_PARCIAL, ESTADO_ANULADO_TOTAL],
}


@dataclass
class Comprobante:
    id: Optional[int]
    empresa_id: int
    cliente_id: int
    serie_id: int
    numero: int
    fecha: object  # date
    tipo: str
    estado: str = ESTADO_BORRADOR
    subtotal: Decimal = Decimal("0")
    igv: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    xml_firmado: Optional[str] = None
    zip_path: Optional[str] = None
    sunat_ticket: Optional[str] = None
    detalles: list = field(default_factory=list)
    activo: bool = True

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS_VALIDOS:
            raise ReglaNegocioViolada(
                f"Tipo de comprobante invalido: {self.tipo}"
            )
        if self.estado not in ESTADOS_VALIDOS:
            raise ReglaNegocioViolada(
                f"Estado invalido: {self.estado}"
            )
        if self.numero <= 0:
            raise ReglaNegocioViolada(
                "El numero de comprobante debe ser positivo"
            )

    # ------------------------------------------------------------
    # Logica de negocio: transiciones de estado
    # ------------------------------------------------------------

    def cambiar_estado(self, nuevo: str) -> None:
        """Cambia el estado validando la transicion."""
        if nuevo not in ESTADOS_VALIDOS:
            raise EstadoInvalido(f"Estado invalido: {nuevo}")
        permitidas = TRANSICIONES_VALIDAS.get(self.estado, [])
        if nuevo not in permitidas:
            raise EstadoInvalido(
                f"No se puede pasar de {self.estado} a {nuevo}. "
                f"Transiciones validas: {permitidas}"
            )
        self.estado = nuevo

    def puede_ser_eliminado(self) -> bool:
        """Regla: ACEPTADO no se elimina, se anula via NC."""
        return self.estado != ESTADO_ACEPTADO

    def es_factura(self) -> bool:
        return self.tipo == TIPO_FACTURA

    def es_boleta(self) -> bool:
        return self.tipo == TIPO_BOLETA

    # ------------------------------------------------------------
    # Calculos tributarios
    # ------------------------------------------------------------

    def calcular_totales(self, tasa_igv: Decimal) -> None:
        """Calcula subtotal, IGV y total del comprobante."""
        subtotal = Decimal("0")
        igv = Decimal("0")
        for det in self.detalles:
            det.calcular_subtotal(tasa_igv)
            subtotal += det.subtotal
            igv += det.igv_linea
        self.subtotal = subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.igv = igv.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total = (self.subtotal + self.igv).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    @property
    def nombre_archivo(self) -> str:
        prefijo = self.tipo or ""
        # serie puede ser un int (id) o un string; manejamos ambos casos
        serie_str = str(self.serie_id) if self.serie_id else ""
        return f"comprobante-{prefijo}-{serie_str}-{self.numero:08d}"

    @property
    def numero_formateado(self) -> str:
        return f"{self.numero:08d}"