"""
Service Layer para el módulo de Comprobantes.

Toda la lógica de negocio de emisión de facturas, boletas, cálculo de IGV
y numeración correlativa está aquí. Las Views solo reciben el request,
llaman al servicio y devuelven el response.
"""

from decimal import Decimal
from django.db import transaction
from django.db.models import Max
from django.conf import settings

from apps.comprobantes.models import (
    Comprobante, DetalleComprobante, SerieComprobante, LogEnvioSUNAT
)
from apps.empresas.models import Empresa
from apps.clientes.models import Cliente
from apps.productos.models import Producto
from apps.core.exceptions import (
    TipoDocumentoInvalido,
    EstadoInvalido,
    ComprobanteNoAnulable,
    SerieNoEncontrada,
    ComprobanteNoEncontrado,
    EmpresaNoEncontrada,
    ClienteNoEncontrado,
    ProductoNoEncontrado,
)


class NumeracionService:
    """Garantiza correlativo sin saltos usando select_for_update()."""

    @staticmethod
    @transaction.atomic
    def siguiente_correlativo(empresa: Empresa, tipo: str) -> tuple:
        """
        Obtiene la serie y el siguiente número correlativo para un tipo de comprobante.
        Usa select_for_update() para evitar condiciones de carrera.

        Returns:
            tuple: (SerieComprobante, int) — la serie y el número siguiente
        Raises:
            SerieNoEncontrada: si no hay serie activa para ese tipo/empresa
        """
        serie_default = {
            '01': 'F001',
            '03': 'B001',
            '07': 'FC01',
            '08': 'FD01',
        }

        serie_obj, created = SerieComprobante.objects.select_for_update().get_or_create(
            empresa=empresa,
            tipo=tipo,
            defaults={
                'serie': serie_default.get(tipo, 'X001'),
                'correlativo_actual': 0,
            }
        )

        if not created:
            serie_obj.refresh_from_db()

        # Recalcular desde BD real para evitar desincronizaciones
        max_numero_real = Comprobante.objects.filter(
            serie=serie_obj
        ).aggregate(Max('numero'))['numero__max'] or 0

        siguiente = max(serie_obj.correlativo_actual, max_numero_real) + 1
        serie_obj.correlativo_actual = siguiente
        serie_obj.save(update_fields=['correlativo_actual'])

        return serie_obj, siguiente


class ComprobanteService:
    """Lógica de negocio para creación y gestión de comprobantes."""

    @staticmethod
    @transaction.atomic
    def crear(data: dict, usuario=None) -> Comprobante:
        """
        Crea un comprobante con sus líneas de detalle.

        Args:
            data: dict con empresa_id, cliente_id, fecha, tipo, detalles
            usuario: User que crea el comprobante

        Returns:
            Comprobante creado

        Raises:
            EmpresaNoEncontrada, ClienteNoEncontrado, ProductoNoEncontrado,
            TipoDocumentoInvalido
        """
        # Obtener entidades
        try:
            empresa = Empresa.objects.get(id=data['empresa_id'])
        except Empresa.DoesNotExist:
            raise EmpresaNoEncontrada(
                f"No existe una Empresa con id={data['empresa_id']}"
            )

        try:
            cliente = Cliente.objects.get(id=data['cliente_id'])
        except Cliente.DoesNotExist:
            raise ClienteNoEncontrado(
                f"No existe un Cliente con id={data['cliente_id']}"
            )

        tipo = data['tipo']

        # Validación tributaria: Factura requiere RUC
        if tipo == '01' and cliente.tipo_doc != '6':
            raise TipoDocumentoInvalido(
                "Para emitir una factura el cliente debe tener RUC (tipo_doc=6). "
                f"El cliente {cliente.razon_social} tiene tipo_doc={cliente.get_tipo_doc_display()}."
            )

        # Validación tributaria: Boleta requiere DNI
        if tipo == '03' and cliente.tipo_doc not in ('1', '4', '7', 'A'):
            raise TipoDocumentoInvalido(
                "Para emitir una boleta el cliente debe tener DNI, CE o Pasaporte. "
                f"El cliente {cliente.razon_social} tiene tipo_doc={cliente.get_tipo_doc_display()}."
            )

        # Numeración correlativa atómica
        serie_obj, numero = NumeracionService.siguiente_correlativo(empresa, tipo)

        comprobante = Comprobante.objects.create(
            empresa=empresa,
            cliente=cliente,
            serie=serie_obj,
            numero=numero,
            fecha=data['fecha'],
            tipo=tipo,
            estado='BORRADOR',
            creado_por=usuario,
        )

        # Crear detalles y calcular totales
        tasa_igv = Decimal(str(settings.IGV_TASA))
        subtotal_total = Decimal('0.00')
        igv_total = Decimal('0.00')

        for det in data.get('detalles', []):
            try:
                producto = Producto.objects.get(id=det['producto_id'])
            except Producto.DoesNotExist:
                raise ProductoNoEncontrado(
                    f"No existe un Producto con id={det['producto_id']}"
                )

            cantidad = Decimal(str(det['cantidad']))
            precio_unitario = Decimal(str(det.get('precio_unitario', producto.precio_unitario)))
            afecto_igv = producto.afecto_igv

            base = precio_unitario * cantidad
            igv_linea = round(base * tasa_igv, 2) if afecto_igv else Decimal('0.00')

            DetalleComprobante.objects.create(
                comprobante=comprobante,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=Decimal(str(det.get('descuento', 0))),
                afecto_igv=afecto_igv,
                cod_tipo_afectacion=producto.cod_tipo_afectacion,
                igv_linea=igv_linea,
                subtotal=base,
                creado_por=usuario,
            )

            subtotal_total += base
            igv_total += igv_linea

        comprobante.subtotal = subtotal_total
        comprobante.igv = igv_total
        comprobante.total = subtotal_total + igv_total
        comprobante.save(update_fields=['subtotal', 'igv', 'total'])

        return comprobante

    @staticmethod
    def emitir(comprobante_id: int) -> Comprobante:
        """
        Cambia estado BORRADOR → EMITIDO y genera XML.

        Raises:
            ComprobanteNoEncontrado, EstadoInvalido
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        repo = ComprobanteRepositoryDjango()
        comprobante = repo.obtener_por_id(comprobante_id)

        if comprobante.estado != 'BORRADOR':
            raise EstadoInvalido(
                f"Solo se pueden emitir comprobantes en estado BORRADOR. "
                f"Estado actual: {comprobante.estado}"
            )

        from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml

        xml_content = generar_xml_ubl(comprobante)
        xml_firmado = firmar_xml(xml_content, empresa_id=comprobante.empresa_id)
        comprobante.xml_firmado = (
            xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        )
        comprobante.estado = 'EMITIDO'
        repo.guardar(comprobante)

        return comprobante

    @staticmethod
    def reenviar(comprobante_id: int) -> Comprobante:
        """
        Reenvía un comprobante RECHAZADO — regenera XML y cambia estado a ENVIADO.

        Raises:
            ComprobanteNoEncontrado, EstadoInvalido
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        repo = ComprobanteRepositoryDjango()
        comprobante = repo.obtener_por_id(comprobante_id)

        if comprobante.estado != 'RECHAZADO':
            raise EstadoInvalido(
                f"Solo se pueden reenviar comprobantes en estado RECHAZADO. "
                f"Estado actual: {comprobante.estado}"
            )

        from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml

        xml_content = generar_xml_ubl(comprobante)
        xml_firmado = firmar_xml(xml_content, empresa_id=comprobante.empresa_id)
        comprobante.xml_firmado = (
            xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
        )
        comprobante.estado = 'ENVIADO'
        repo.guardar(comprobante)

        return comprobante

    @staticmethod
    def cambiar_estado(comprobante_id: int, nuevo_estado: str) -> Comprobante:
        """
        Cambia el estado de un comprobante validando las transiciones permitidas.

        Raises:
            ComprobanteNoEncontrado, EstadoInvalido
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        repo = ComprobanteRepositoryDjango()
        comprobante = repo.obtener_por_id(comprobante_id)

        transiciones = Comprobante.TRANSICIONES_VALIDAS.get(comprobante.estado, [])
        if nuevo_estado not in transiciones:
            raise EstadoInvalido(
                f"No se puede pasar de {comprobante.estado} a {nuevo_estado}. "
                f"Transiciones válidas: {transiciones}"
            )

        comprobante.estado = nuevo_estado
        repo.guardar(comprobante)
        return comprobante

    @staticmethod
    def eliminar(comprobante_id: int, usuario=None) -> None:
        """
        Soft delete de un comprobante. ACEPTADO no se puede eliminar.

        Raises:
            ComprobanteNoEncontrado, ComprobanteNoAnulable
        """
        from apps.comprobantes.repositories import ComprobanteRepositoryDjango
        repo = ComprobanteRepositoryDjango()
        comprobante = repo.obtener_por_id(comprobante_id)

        if comprobante.estado == 'ACEPTADO':
            raise ComprobanteNoAnulable(
                "Un comprobante ACEPTADO no se puede eliminar. "
                "Solo se puede anular mediante una Nota de Crédito."
            )

        comprobante.eliminar(usuario=usuario)
