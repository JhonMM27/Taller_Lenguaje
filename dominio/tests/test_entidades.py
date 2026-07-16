"""
Tests del dominio: entidades puras con dataclasses.

Estos tests NO importan Django y NO usan base de datos.
Validan la logica de negocio aislada.
"""
import pytest
from decimal import Decimal
from datetime import date

from dominio.entidades.comprobante import (
    Comprobante,
    DetalleComprobante,
    SerieComprobante,
    ESTADO_BORRADOR,
    ESTADO_EMITIDO,
    ESTADO_ENVIADO,
    ESTADO_ACEPTADO,
    ESTADO_RECHAZADO,
    ESTADO_ANULADO_TOTAL,
    TIPO_FACTURA,
    TIPO_BOLETA,
    TIPO_NOTA_CREDITO,
    TRANSICIONES_VALIDAS,
)
from dominio.excepciones import (
    DomainError,
    EstadoInvalido,
    ReglaNegocioViolada,
)


class TestComprobanteEntidad:
    """Tests de la entidad Comprobante sin BD."""

    def test_crear_comprobante_basico(self):
        c = Comprobante(
            id=None,
            empresa_id=1,
            cliente_id=2,
            serie_id=1,
            numero=1,
            fecha=date.today(),
            tipo=TIPO_FACTURA,
        )
        assert c.tipo == TIPO_FACTURA
        assert c.estado == ESTADO_BORRADOR
        assert c.total == Decimal("0")

    def test_tipo_invalido_lanza_error(self):
        with pytest.raises(ReglaNegocioViolada):
            Comprobante(
                id=None,
                empresa_id=1, cliente_id=2, serie_id=1, numero=1,
                fecha=date.today(),
                tipo="99",  # invalido
            )

    def test_numero_negativo_lanza_error(self):
        with pytest.raises(ReglaNegocioViolada):
            Comprobante(
                id=None,
                empresa_id=1, cliente_id=2, serie_id=1, numero=0,
                fecha=date.today(),
                tipo=TIPO_FACTURA,
            )

    def test_transicion_valida_borrador_a_emitido(self):
        c = self._comprobante()
        c.cambiar_estado(ESTADO_EMITIDO)
        assert c.estado == ESTADO_EMITIDO

    def test_transicion_invalida_lanza_error(self):
        c = self._comprobante()
        c.cambiar_estado(ESTADO_EMITIDO)
        c.cambiar_estado(ESTADO_ENVIADO)
        c.cambiar_estado(ESTADO_ACEPTADO)
        # ACEPTADO solo puede ir a ANULADO_*
        with pytest.raises(EstadoInvalido):
            c.cambiar_estado(ESTADO_BORRADOR)

    def test_aceptado_no_se_puede_eliminar(self):
        c = self._comprobante()
        c.cambiar_estado(ESTADO_EMITIDO)
        c.cambiar_estado(ESTADO_ENVIADO)
        c.cambiar_estado(ESTADO_ACEPTADO)
        assert not c.puede_ser_eliminado()

    def test_borrador_si_se_puede_eliminar(self):
        c = self._comprobante()
        assert c.puede_ser_eliminado()

    def test_es_factura_y_es_boleta(self):
        c1 = Comprobante(
            id=None, empresa_id=1, cliente_id=2, serie_id=1, numero=1,
            fecha=date.today(), tipo=TIPO_FACTURA,
        )
        c2 = Comprobante(
            id=None, empresa_id=1, cliente_id=2, serie_id=1, numero=1,
            fecha=date.today(), tipo=TIPO_BOLETA,
        )
        assert c1.es_factura()
        assert not c1.es_boleta()
        assert c2.es_boleta()
        assert not c2.es_factura()

    @staticmethod
    def _comprobante():
        return Comprobante(
            id=None,
            empresa_id=1, cliente_id=2, serie_id=1, numero=1,
            fecha=date.today(),
            tipo=TIPO_FACTURA,
        )


class TestDetalleComprobanteEntidad:
    """Tests del DetalleComprobante."""

    def test_detalle_valido(self):
        d = DetalleComprobante(
            id=None,
            producto_id=1,
            cantidad=Decimal("2"),
            precio_unitario=Decimal("100"),
            afecto_igv=True,
        )
        assert d.cantidad == Decimal("2")

    def test_cantidad_negativa_lanza_error(self):
        with pytest.raises(ReglaNegocioViolada):
            DetalleComprobante(
                id=None, producto_id=1,
                cantidad=Decimal("0"),
                precio_unitario=Decimal("100"),
            )

    def test_calcular_subtotal_con_igv(self):
        d = DetalleComprobante(
            id=None, producto_id=1,
            cantidad=Decimal("2"),
            precio_unitario=Decimal("100"),
            afecto_igv=True,
        )
        base = d.calcular_subtotal(Decimal("0.18"))
        assert base == Decimal("200.00")
        assert d.subtotal == Decimal("200.00")
        assert d.igv_linea == Decimal("36.00")
        assert d.total_linea == Decimal("236.00")

    def test_calcular_subtotal_sin_igv(self):
        d = DetalleComprobante(
            id=None, producto_id=1,
            cantidad=Decimal("1"),
            precio_unitario=Decimal("100"),
            afecto_igv=False,
        )
        d.calcular_subtotal(Decimal("0.18"))
        assert d.subtotal == Decimal("100.00")
        assert d.igv_linea == Decimal("0.00")


class TestSerieComprobanteEntidad:
    def test_siguiente_correlativo(self):
        s = SerieComprobante(
            id=None, empresa_id=1, tipo=TIPO_FACTURA,
            serie="F001", correlativo_actual=5,
        )
        assert s.siguiente_correlativo == 6
        assert s.reservar_siguiente() == 6
        assert s.correlativo_actual == 6

    def test_tipo_invalido(self):
        with pytest.raises(ReglaNegocioViolada):
            SerieComprobante(
                id=None, empresa_id=1, tipo="99",
                serie="F001", correlativo_actual=0,
            )


class TestComprobanteTotales:
    """Tests de calculo de totales integrado."""

    def test_calcular_totales_con_dos_detalles(self):
        c = Comprobante(
            id=None, empresa_id=1, cliente_id=2, serie_id=1, numero=1,
            fecha=date.today(), tipo=TIPO_FACTURA,
            detalles=[
                DetalleComprobante(
                    id=None, producto_id=1,
                    cantidad=Decimal("2"),
                    precio_unitario=Decimal("100"),
                    afecto_igv=True,
                ),
                DetalleComprobante(
                    id=None, producto_id=2,
                    cantidad=Decimal("1"),
                    precio_unitario=Decimal("50"),
                    afecto_igv=False,
                ),
            ],
        )
        c.calcular_totales(Decimal("0.18"))
        assert c.subtotal == Decimal("250.00")
        assert c.igv == Decimal("36.00")
        assert c.total == Decimal("286.00")


class TestExcepciones:
    """Tests de la jerarquia de excepciones del dominio."""

    def test_herencia(self):
        from dominio.excepciones import (
            EstadoInvalido, TipoDocumentoInvalido, ComprobanteNoAnulable,
            RecursoNoEncontrado, ComprobanteNoEncontrado,
        )
        assert issubclass(EstadoInvalido, DomainError)
        assert issubclass(TipoDocumentoInvalido, DomainError)
        assert issubclass(ComprobanteNoAnulable, DomainError)
        assert issubclass(ComprobanteNoEncontrado, RecursoNoEncontrado)

    def test_mensaje(self):
        e = EstadoInvalido("transicion invalida")
        assert str(e) == "transicion invalida"