"""
Backward-compatibility: re-exporta el service de dominio desde `interfaces.container`.

Las views viejas hacen `from apps.comprobantes.services import ComprobanteService`.
Para no romperlas, este modulo expone una clase-compatible que delega al
servicio del dominio via DI y devuelve modelos Django ORM (manteniendo
la firma original).

IMPORTANTE: emitir()/reenviar() NO usan el repositorio hexagonal para
guardar, porque el hexagonal borra los detalles. Usamos Django ORM directo
para preservar los detalles existentes.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP

from interfaces.container import (
    get_comprobante_service,
    get_uow,
)


logger = logging.getLogger(__name__)


def _validar_tipo_cliente(tipo, cliente, tipo_operacion='0101'):
    from dominio.entidades.cliente import LONGITUDES_DOC, TIPOS_DOC_VALIDOS
    from dominio.excepciones import TipoDocumentoInvalido

    if cliente.tipo_doc not in TIPOS_DOC_VALIDOS:
        raise TipoDocumentoInvalido(
            f"Tipo de documento del receptor no permitido: {cliente.tipo_doc}."
        )
    if tipo_operacion == '0200':
        if tipo != '01':
            raise TipoDocumentoInvalido(
                "La exportacion de bienes 0200 debe emitirse como factura."
            )
        if cliente.tipo_doc not in ('0', '4', '7', 'A'):
            raise TipoDocumentoInvalido(
                "La exportacion requiere un receptor no domiciliado con documento extranjero."
            )
        if str(getattr(cliente, 'pais_codigo', 'PE') or 'PE').upper() == 'PE':
            raise TipoDocumentoInvalido(
                "El receptor de una exportacion debe residir fuera de Peru."
            )
    elif tipo == '01' and cliente.tipo_doc != '6':
        if (
            cliente.tipo_doc in ('0', '4', '7', 'A')
            and str(getattr(cliente, 'pais_codigo', 'PE') or 'PE').upper() != 'PE'
        ):
            raise TipoDocumentoInvalido(
                "El receptor es extranjero. Para emitirle una factura de exportacion "
                "seleccione exclusivamente productos con afectacion IGV 40; el sistema "
                "generara automaticamente la operacion 0200."
            )
        raise TipoDocumentoInvalido(
            "SUNAT exige RUC (tipo 6) para una factura nacional. "
            "Seleccione un cliente con RUC o genere una boleta."
        )
    esperado = LONGITUDES_DOC.get(cliente.tipo_doc)
    numero = str(cliente.num_doc or '').strip()
    if esperado and (not numero.isdigit() or len(numero) != esperado):
        raise TipoDocumentoInvalido(
            f"El documento tipo {cliente.tipo_doc} debe contener {esperado} digitos."
        )


def _tipo_operacion_desde_detalles(detalles_data):
    from apps.productos.models import Producto
    from dominio.tributos import tipo_operacion_comprobante

    codigos = []
    for data in detalles_data:
        codigo = data.get('cod_tipo_afectacion')
        if not codigo:
            codigo = Producto.objects.only('cod_tipo_afectacion').get(
                pk=int(data['producto_id'])
            ).cod_tipo_afectacion
        codigos.append(str(codigo))
    return tipo_operacion_comprobante(codigos)


def _reemplazar_detalles(modelo, detalles_data, moneda=None):
    """Reemplaza lineas y recalcula importes usando la afectacion SUNAT de cada item."""
    from apps.productos.models import Producto
    from apps.comprobantes.models import DetalleComprobante
    from dominio.tributos import (
        datos_afectacion_igv,
        tipo_operacion_comprobante,
        validar_moneda,
    )
    from dominio.excepciones import ReglaNegocioViolada, ProductoNoEncontrado

    if not detalles_data:
        raise ReglaNegocioViolada("Debe incluir al menos un producto.")

    lineas = []
    subtotal_total = Decimal('0.00')
    igv_total = Decimal('0.00')
    for data in detalles_data:
        try:
            producto = Producto.objects.get(pk=int(data['producto_id']), activo=True)
        except (Producto.DoesNotExist, TypeError, ValueError, KeyError) as exc:
            raise ProductoNoEncontrado("Uno de los productos seleccionados no existe.") from exc

        cantidad = Decimal(str(data.get('cantidad', '1')))
        precio = Decimal(str(data.get('precio_unitario', producto.precio_unitario)))
        descuento = Decimal(str(data.get('descuento', '0') or '0'))
        if cantidad <= 0 or precio < 0 or descuento < 0 or descuento > precio:
            raise ReglaNegocioViolada(
                "Cantidad, precio o descuento invalido en una linea del comprobante."
            )

        codigo = str(data.get('cod_tipo_afectacion') or producto.cod_tipo_afectacion)
        tributo = datos_afectacion_igv(codigo)
        base = ((precio - descuento) * cantidad).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        if tributo['gratuito']:
            subtotal = Decimal('0.00')
            igv_linea = Decimal('0.00')
        else:
            subtotal = base
            igv_linea = (base * tributo['tasa'] / Decimal('100')).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
        lineas.append(DetalleComprobante(
            comprobante=modelo,
            producto=producto,
            cantidad=cantidad,
            precio_unitario=precio,
            descuento=descuento,
            afecto_igv=codigo in ('10', '17'),
            cod_tipo_afectacion=codigo,
            subtotal=subtotal,
            igv_linea=igv_linea,
        ))
        subtotal_total += subtotal
        igv_total += igv_linea

    modelo.detalles.all().delete()
    DetalleComprobante.objects.bulk_create(lineas)
    modelo.subtotal = subtotal_total
    modelo.igv = igv_total
    modelo.total = subtotal_total + igv_total
    modelo.tipo_operacion = tipo_operacion_comprobante(
        linea.cod_tipo_afectacion for linea in lineas
    )
    modelo.moneda = validar_moneda(moneda or modelo.moneda)
    _validar_tipo_cliente(modelo.tipo, modelo.cliente, modelo.tipo_operacion)
    modelo.xml_firmado = None
    modelo.zip_path = None
    modelo.sunat_ticket = None
    modelo.save(update_fields=[
        'subtotal', 'igv', 'total', 'tipo_operacion', 'moneda',
        'xml_firmado', 'zip_path', 'sunat_ticket'
    ])


def _modelo_desde_entidad(ent):
    """Helper: dado una entidad de dominio, devuelve el modelo Django."""
    if ent is None or ent.id is None:
        return None
    from apps.comprobantes.models import Comprobante as CompModel
    return CompModel.objects.select_related(
        'cliente', 'empresa', 'serie'
    ).get(pk=ent.id)


def _generar_y_firmar_xml(comprobante_model):
    """
    Genera el XML UBL 2.1 del comprobante y lo firma digitalmente.

    Retorna el XML firmado (str) o None si falla.
    """
    try:
        from apps.sunat_ose.xml_generator import generar_xml_ubl
        from apps.sunat_ose.firmar import firmar_xml

        xml_content = generar_xml_ubl(comprobante_model)
        xml_firmado = firmar_xml(xml_content, empresa_id=comprobante_model.empresa_id)
        if isinstance(xml_firmado, bytes):
            return xml_firmado.decode('utf-8')
        return xml_firmado
    except Exception as exc:
        logger.exception("Error generando/firmando XML para comprobante %s", comprobante_model.pk)
        return None


class ComprobanteService:
    """Wrapper backward-compatible para views/templates que importan
    desde `apps.comprobantes.services`.

    Mantiene la firma clasica (devuelve modelos Django) pero delega
    a la nueva capa hexagonal.
    """

    @staticmethod
    def crear(data, usuario=None):
        creado_por_id = usuario.id if usuario else None
        detalles = data.get('detalles', [])
        service = get_comprobante_service()
        ent = service.crear(
            empresa_id=data['empresa_id'],
            cliente_id=data['cliente_id'],
            fecha=data['fecha'],
            tipo=data['tipo'],
            detalles_data=detalles,
            creado_por_id=creado_por_id,
            moneda=data.get('moneda', 'PEN'),
        )
        return _modelo_desde_entidad(ent)

    @staticmethod
    def emitir(comprobante_id):
        """
        Cambia estado BORRADOR -> EMITIDO y genera el XML firmado.
        IMPORTANTE: usa Django ORM directo para preservar los detalles.
        """
        from apps.comprobantes.models import Comprobante as CompModel
        modelo = (
            CompModel.objects
            .select_related('cliente', 'empresa', 'serie')
            .get(pk=comprobante_id, activo=True)
        )

        if modelo.estado != 'BORRADOR':
            from dominio.excepciones import EstadoInvalido
            raise EstadoInvalido(
                f"Solo se pueden emitir comprobantes en BORRADOR. "
                f"Estado actual: {modelo.estado}"
            )

        # Generar y firmar XML
        xml_firmado = _generar_y_firmar_xml(modelo)

        # Actualizar modelo (sin tocar detalles)
        update_fields = ['estado']
        modelo.estado = 'EMITIDO'
        if xml_firmado:
            modelo.xml_firmado = xml_firmado
            update_fields.append('xml_firmado')
        modelo.save(update_fields=update_fields)

        return modelo

    @staticmethod
    def reintentar_envio(comprobante_id):
        """
        Reintenta un fallo tecnico. Un rechazo SUNAT nunca reutiliza numeracion.
        """
        from apps.comprobantes.models import Comprobante as CompModel
        modelo = (
            CompModel.objects
            .select_related('cliente', 'empresa', 'serie')
            .get(pk=comprobante_id, activo=True)
        )

        if modelo.estado != 'ERROR_ENVIO':
            from dominio.excepciones import EstadoInvalido
            raise EstadoInvalido(
                f"Solo se pueden reintentar comprobantes con ERROR_ENVIO. "
                f"Estado actual: {modelo.estado}"
            )

        from apps.sunat_ose.services import SunatEnvioService
        SunatEnvioService.enviar(comprobante_id)
        modelo.refresh_from_db()

        return modelo

    # Alias compatible: conserva llamadas antiguas pero aplica la regla segura.
    reenviar = reintentar_envio

    @staticmethod
    def actualizar_borrador(comprobante_id, data, usuario=None):
        """Edita receptor, fecha y lineas sin alterar empresa/tipo/numeracion."""
        from django.db import transaction
        from apps.comprobantes.models import Comprobante as CompModel
        from apps.clientes.models import Cliente
        from dominio.excepciones import EstadoInvalido, ClienteNoEncontrado

        with transaction.atomic():
            modelo = CompModel.objects.select_for_update().get(
                pk=comprobante_id, activo=True
            )
            if modelo.estado != 'BORRADOR':
                raise EstadoInvalido(
                    "Solo se pueden editar directamente comprobantes en BORRADOR."
                )
            try:
                cliente = Cliente.objects.get(pk=data['cliente_id'], activo=True)
            except Cliente.DoesNotExist as exc:
                raise ClienteNoEncontrado("El cliente seleccionado no existe.") from exc
            modelo.cliente = cliente
            modelo.fecha = data['fecha']
            modelo.save(update_fields=['cliente', 'fecha'])
            _reemplazar_detalles(modelo, data['detalles'], data.get('moneda'))
        return modelo

    @staticmethod
    def corregir_rechazado(comprobante_id, data, usuario=None):
        """Genera un documento nuevo y conserva inmutable el rechazo original."""
        from django.db import transaction, IntegrityError
        from apps.comprobantes.models import Comprobante as CompModel
        from apps.clientes.models import Cliente
        from dominio.excepciones import EstadoInvalido, ClienteNoEncontrado

        try:
            with transaction.atomic():
                original = CompModel.objects.select_for_update().get(
                    pk=comprobante_id, activo=True
                )
                if original.estado != 'RECHAZADO':
                    raise EstadoInvalido(
                        "Solo se pueden reemplazar comprobantes rechazados por SUNAT/OSE."
                    )
                if CompModel.objects.filter(reemplaza_a=original).exists():
                    raise EstadoInvalido(
                        "Este comprobante ya tiene un documento de reemplazo."
                    )
                try:
                    cliente = Cliente.objects.get(pk=data['cliente_id'], activo=True)
                except Cliente.DoesNotExist as exc:
                    raise ClienteNoEncontrado("El cliente seleccionado no existe.") from exc

                tipo_operacion = _tipo_operacion_desde_detalles(data['detalles'])
                tipo_nuevo = '01' if (
                    tipo_operacion == '0200' or cliente.tipo_doc == '6'
                ) else '03'
                _validar_tipo_cliente(tipo_nuevo, cliente, tipo_operacion)
                nuevo = ComprobanteService.crear(
                    data={
                        'empresa_id': original.empresa_id,
                        'cliente_id': cliente.id,
                        'fecha': data['fecha'],
                        'tipo': tipo_nuevo,
                        'moneda': data.get('moneda', original.moneda),
                        'detalles': data['detalles'],
                    },
                    usuario=usuario,
                )
                nuevo.reemplaza_a = original
                nuevo.save(update_fields=['reemplaza_a'])
                return nuevo
        except IntegrityError as exc:
            raise EstadoInvalido(
                "Este comprobante ya fue reemplazado por otro documento."
            ) from exc

    @staticmethod
    def eliminar(comprobante_id, usuario=None):
        return get_comprobante_service().eliminar(
            comprobante_id=comprobante_id,
            usuario_id=usuario.id if usuario else None,
        )

    @staticmethod
    def cambiar_estado(comprobante_id, nuevo_estado):
        from apps.comprobantes.models import Comprobante as CompModel
        modelo = (
            CompModel.objects
            .select_related('cliente', 'empresa', 'serie')
            .get(pk=comprobante_id, activo=True)
        )
        from dominio.excepciones import EstadoInvalido
        transiciones = CompModel.TRANSICIONES_VALIDAS.get(modelo.estado, [])
        if nuevo_estado not in transiciones:
            raise EstadoInvalido(
                f"No se puede pasar de {modelo.estado} a {nuevo_estado}. "
                f"Transiciones validas: {transiciones}"
            )
        modelo.estado = nuevo_estado
        modelo.save(update_fields=['estado'])
        return modelo


class NumeracionService:
    """Wrapper backward-compatible para NumeracionService."""

    @staticmethod
    def siguiente_correlativo(empresa, tipo):
        from interfaces.container import get_uow
        return get_uow().series.siguiente_correlativo(empresa.id, tipo)


__all__ = ['ComprobanteService', 'NumeracionService']
