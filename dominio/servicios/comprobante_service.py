"""
Servicio de dominio: ComprobanteService.

Caso de uso principal: emitir comprobantes electronicos (facturas/boletas).
Toda la logica de negocio tributaria vive aqui. NO toca Django ni el ORM.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from ..entidades.comprobante import (
    Comprobante,
    DetalleComprobante,
    ESTADO_BORRADOR,
    ESTADO_EMITIDO,
    TIPO_FACTURA,
    TIPO_BOLETA,
)
from ..eventos import (
    ComprobanteCreado,
    ComprobanteEmitido,
    ComprobanteEliminado,
)
from ..excepciones import (
    ClienteNoEncontrado,
    ComprobanteNoAnulable,
    ComprobanteNoEncontrado,
    EmpresaNoEncontrada,
    EstadoInvalido,
    ProductoNoEncontrado,
    ReglaNegocioViolada,
    TipoDocumentoInvalido,
)
from ..puertos.repositorios import (
    IClienteRepository,
    IComprobanteRepository,
    IProductoRepository,
    IUnitOfWork,
)
from ..tributos import (
    TIPO_OPERACION_EXPORTACION_BIENES,
    datos_afectacion_igv,
    tipo_operacion_comprobante,
    validar_moneda,
)


# Tasa IGV por defecto. Las implementaciones pueden sobreescribirla.
IGV_TASA = Decimal("0.18")


class _EventBus(Protocol):
    """Protocol minimo para publicar eventos (desacoplado)."""
    def publish(self, event) -> None: ...


class ComprobanteService:
    """
    Caso de uso para gestion de comprobantes electronicos.

    Dependencias inyectadas:
        uow: IUnitOfWork
        event_bus: publicador de eventos (opcional)
        tasa_igv: Decimal (default 0.18)
    """

    def __init__(
        self,
        uow: IUnitOfWork,
        event_bus: Optional[_EventBus] = None,
        tasa_igv: Decimal = IGV_TASA,
    ) -> None:
        self._uow = uow
        self._events = event_bus
        self._tasa_igv = Decimal(str(tasa_igv))

    # ------------------------------------------------------------
    # Casos de uso publicos
    # ------------------------------------------------------------

    def crear(
        self,
        empresa_id: int,
        cliente_id: int,
        fecha: date,
        tipo: str,
        detalles_data: list[dict],
        creado_por_id: Optional[int] = None,
        moneda: str = "PEN",
    ) -> Comprobante:
        """Crea un comprobante en estado BORRADOR con sus detalles.

        Validaciones:
            - Empresa existe.
            - Cliente existe.
            - Reglas tributarias (factura requiere RUC, boleta DNI/CE/Pasaporte).
            - Numeracion correlativa atomica.
        """
        empresa = self._obtener_empresa(empresa_id)
        cliente = self._uow.clientes.obtener_por_id(cliente_id)
        detalles = [
            self._construir_detalle(d) for d in detalles_data
        ]
        try:
            tipo_operacion = tipo_operacion_comprobante(
                detalle.cod_tipo_afectacion for detalle in detalles
            )
            moneda = validar_moneda(moneda)
        except ValueError as exc:
            raise ReglaNegocioViolada(str(exc)) from exc
        self._validar_tipo_documento(tipo, cliente, tipo_operacion)

        with self._uow:
            # siguiente_correlativo usa select_for_update → debe correr dentro de una transacción
            serie, numero = self._uow.series.siguiente_correlativo(empresa_id, tipo)

            comprobante = Comprobante(
                id=None,
                empresa_id=empresa_id,
                cliente_id=cliente_id,
                serie_id=serie.id if serie.id else 0,
                numero=numero,
                fecha=fecha,
                tipo=tipo,
                tipo_operacion=tipo_operacion,
                moneda=moneda,
                estado=ESTADO_BORRADOR,
                detalles=detalles,
            )
            comprobante.calcular_totales(self._tasa_igv)

            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.commit()

        if self._events is not None:
            self._events.publish(ComprobanteCreado(
                comprobante_id=guardado.id,
                empresa_id=empresa_id,
                tipo=tipo,
                numero=numero,
                total=guardado.total,
                creado_por_id=creado_por_id,
            ))

        return guardado


    def emitir(
        self,
        comprobante_id: int,
        xml_content: Optional[str] = None,
    ) -> Comprobante:
        """Cambia el estado BORRADOR -> EMITIDO. Valida transicion."""
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        if comprobante.estado != ESTADO_BORRADOR:
            raise EstadoInvalido(
                f"Solo se pueden emitir comprobantes en BORRADOR. "
                f"Estado actual: {comprobante.estado}"
            )
        comprobante.cambiar_estado(ESTADO_EMITIDO)
        if xml_content is not None:
            comprobante.xml_firmado = xml_content

        with self._uow:
            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.commit()

        if self._events is not None:
            self._events.publish(ComprobanteEmitido(
                comprobante_id=guardado.id,
                empresa_id=guardado.empresa_id,
                xml_firmado=bool(xml_content),
            ))
        return guardado

    def reenviar(
        self,
        comprobante_id: int,
        xml_content: Optional[str] = None,
    ) -> Comprobante:
        """Reenvia un comprobante RECHAZADO regenerando XML."""
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        if comprobante.estado != "RECHAZADO":
            raise EstadoInvalido(
                f"Solo se pueden reenviar comprobantes RECHAZADOS. "
                f"Estado actual: {comprobante.estado}"
            )
        if xml_content is not None:
            comprobante.xml_firmado = xml_content
        comprobante.estado = "ENVIADO"
        with self._uow:
            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.commit()
        return guardado

    def marcar_aceptado(
        self,
        comprobante_id: int,
        ticket: Optional[str] = None,
        cdr: str = "",
    ) -> Comprobante:
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        comprobante.estado = "ACEPTADO"
        comprobante.sunat_ticket = ticket
        with self._uow:
            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.logs_sunat.registrar(
                guardado,
                estado_respuesta="ACEPTADO",
                codigo_respuesta="0",
                descripcion="CDR recibido - Comprobante aceptado por SUNAT/OSE",
                uuid=ticket or "",
                cdr_xml=cdr,
            )
            self._uow.commit()
        return guardado

    def marcar_rechazado(
        self,
        comprobante_id: int,
        motivo: str,
        codigo: str = "-1",
    ) -> Comprobante:
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        comprobante.estado = "RECHAZADO"
        with self._uow:
            guardado = self._uow.comprobantes.guardar(comprobante)
            self._uow.logs_sunat.registrar(
                guardado,
                estado_respuesta="RECHAZADO",
                codigo_respuesta=codigo,
                descripcion=motivo,
            )
            self._uow.commit()
        return guardado

    def eliminar(
        self,
        comprobante_id: int,
        usuario_id: Optional[int] = None,
    ) -> None:
        """Soft delete. ACEPTADO no se elimina."""
        comprobante = self._uow.comprobantes.obtener_por_id(comprobante_id)
        if not comprobante.puede_ser_eliminado():
            raise ComprobanteNoAnulable(
                "Un comprobante ACEPTADO no se puede eliminar. "
                "Solo se puede anular mediante una Nota de Credito."
            )
        with self._uow:
            self._uow.comprobantes.eliminar_soft(comprobante_id, usuario_id)
            self._uow.commit()
        if self._events is not None:
            self._events.publish(ComprobanteEliminado(
                comprobante_id=comprobante_id,
                eliminado_por_id=usuario_id,
            ))

    def obtener(self, comprobante_id: int) -> Comprobante:
        return self._uow.comprobantes.obtener_por_id(comprobante_id)

    def listar(
        self,
        empresa_id: Optional[int] = None,
        **filtros,
    ) -> list[Comprobante]:
        return self._uow.comprobantes.listar(
            empresa_id=empresa_id, **filtros
        )

    # ------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------

    def _obtener_empresa(self, empresa_id: int):
        return self._uow.empresas.obtener_por_id(empresa_id)

    def _validar_tipo_documento(
        self, tipo: str, cliente, tipo_operacion: str = "0101"
    ) -> None:
        """Valida el documento del receptor y su compatibilidad tributaria."""
        from ..entidades.cliente import LONGITUDES_DOC, TIPOS_DOC_VALIDOS
        esperado = LONGITUDES_DOC.get(cliente.tipo_doc)
        if tipo_operacion == TIPO_OPERACION_EXPORTACION_BIENES:
            if tipo != TIPO_FACTURA:
                raise TipoDocumentoInvalido(
                    "La exportacion de bienes 0200 debe emitirse como factura tipo 01."
                )
            if cliente.tipo_doc == "6" or cliente.tipo_doc not in ("0", "4", "7", "A"):
                raise TipoDocumentoInvalido(
                    "La exportacion requiere un receptor no domiciliado con documento extranjero."
                )
            if str(getattr(cliente, "pais_codigo", "PE") or "PE").upper() == "PE":
                raise TipoDocumentoInvalido(
                    "El receptor de una exportacion debe tener un pais de residencia distinto de PE."
                )
        elif tipo == TIPO_FACTURA and cliente.tipo_doc != "6":
            if (
                cliente.tipo_doc in ("0", "4", "7", "A")
                and str(getattr(cliente, "pais_codigo", "PE") or "PE").upper() != "PE"
            ):
                raise TipoDocumentoInvalido(
                    "El receptor es extranjero. Para emitirle una factura de exportacion "
                    "seleccione exclusivamente productos con afectacion IGV 40; el sistema "
                    "generara automaticamente la operacion 0200."
                )
            raise TipoDocumentoInvalido(
                "SUNAT exige RUC (tipo 6) para el receptor de una factura. "
                "Si el cliente solo tiene DNI, emita una boleta (tipo 03)."
            )
        if esperado and (
            not str(cliente.num_doc).isdigit()
            or len(cliente.num_doc) != esperado
        ):
            nombres = {
                "1": "DNI",
                "4": "Carnet de Extranjeria",
                "6": "RUC",
                "7": "Pasaporte",
                "A": "Cedula de Identidad",
            }
            raise TipoDocumentoInvalido(
                f"El {nombres.get(cliente.tipo_doc, cliente.tipo_doc)} "
                f"debe tener exactamente {esperado} digitos. "
                f"Recibido: {len(cliente.num_doc)}."
            )

    def _construir_detalle(self, data: dict) -> DetalleComprobante:
        producto_id = data["producto_id"]
        try:
            producto = self._uow.productos.obtener_por_id(producto_id)
        except Exception as exc:
            raise ProductoNoEncontrado(
                f"No existe un Producto con id={producto_id}"
            ) from exc

        cantidad = Decimal(str(data.get("cantidad", 1)))
        precio = Decimal(str(
            data.get("precio_unitario", producto.precio_unitario)
        ))

        codigo_afectacion = str(
            data.get("cod_tipo_afectacion") or producto.cod_tipo_afectacion
        )
        datos_afectacion_igv(codigo_afectacion)  # valida contra catalogo SUNAT 07

        return DetalleComprobante(
            id=None,
            producto_id=producto_id,
            cantidad=cantidad,
            precio_unitario=precio,
            descuento=Decimal(str(data.get("descuento", 0))),
            afecto_igv=codigo_afectacion in ("10", "17"),
            cod_tipo_afectacion=codigo_afectacion,
            unidad_medida=producto.unidad_medida,
            descripcion=producto.descripcion,
            codigo_producto=producto.codigo or "",
        )
