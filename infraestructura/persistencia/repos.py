"""
Adaptadores de repositorio: Django ORM -> implementan los puertos del dominio.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from django.db.models import Max

from dominio.entidades import (
    Cliente,
    Producto,
    Comprobante,
    DetalleComprobante,
    NotaCredito,
    DetalleNotaCredito,
    SerieComprobante,
    Empresa,
)
from dominio.excepciones import (
    ClienteNoEncontrado,
    ComprobanteNoEncontrado,
    EmpresaNoEncontrada,
    NotaCreditoNoEncontrada,
    ProductoNoEncontrado,
    SerieNoEncontrada,
)

from .mappers import (
    cliente_a_modelo,
    modelo_a_cliente,
    producto_a_modelo,
    modelo_a_producto,
    comprobante_a_modelo,
    modelo_a_comprobante,
    nota_credito_a_modelo,
    modelo_a_nota_credito,
    serie_a_modelo,
    modelo_a_serie,
    empresa_a_modelo,
    modelo_a_empresa,
    detalle_comprobante_a_modelo,
    modelo_a_detalle_comprobante,
    detalle_nota_credito_a_modelo,
    modelo_a_detalle_nota_credito,
)


# ============================================================
# Empresa
# ============================================================

class DjangoEmpresaRepository:
    def obtener_por_id(self, empresa_id: int) -> Empresa:
        from apps.empresas.models import Empresa as EmpresaModel
        try:
            m = EmpresaModel.objects.get(pk=empresa_id, activo=True)
        except EmpresaModel.DoesNotExist as exc:
            raise EmpresaNoEncontrada(
                f"No existe Empresa con id={empresa_id}"
            ) from exc
        return modelo_a_empresa(m)

    def listar(self, solo_activos: bool = True) -> list[Empresa]:
        from apps.empresas.models import Empresa as EmpresaModel
        qs = EmpresaModel.objects.all()
        if solo_activos:
            qs = qs.filter(activo=True)
        return [modelo_a_empresa(m) for m in qs]

    def guardar(self, empresa: Empresa) -> Empresa:
        from apps.empresas.models import Empresa as EmpresaModel
        m = empresa_a_modelo(empresa)
        m.save()
        return modelo_a_empresa(m)

    def eliminar_soft(self, empresa_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.empresas.models import Empresa as EmpresaModel
        m = EmpresaModel.objects.filter(pk=empresa_id).first()
        if m:
            m.eliminar(usuario=None)


# ============================================================
# Cliente
# ============================================================

class DjangoClienteRepository:
    def obtener_por_id(self, cliente_id: int) -> Cliente:
        from apps.clientes.models import Cliente as ClienteModel
        try:
            m = ClienteModel.activos.get(pk=cliente_id)
        except ClienteModel.DoesNotExist as exc:
            raise ClienteNoEncontrado(
                f"No existe Cliente con id={cliente_id}"
            ) from exc
        return modelo_a_cliente(m)

    def buscar(
        self, query: str = "", solo_activos: bool = True, limit: int = 50
    ) -> list[Cliente]:
        from apps.clientes.models import Cliente as ClienteModel
        from django.db.models import Q
        qs = ClienteModel.objects.all()
        if solo_activos:
            qs = qs.filter(activo=True)
        if query:
            qs = qs.filter(
                Q(razon_social__icontains=query)
                | Q(num_doc__icontains=query)
                | Q(codigo__icontains=query)
            )
        return [modelo_a_cliente(m) for m in qs[:limit]]

    def guardar(self, cliente: Cliente) -> Cliente:
        from apps.clientes.models import Cliente as ClienteModel
        if cliente.id:
            m = ClienteModel.objects.filter(pk=cliente.id).first() or ClienteModel()
        else:
            m = ClienteModel()
        m = cliente_a_modelo(cliente, m)
        m.save()
        return modelo_a_cliente(m)

    def eliminar_soft(self, cliente_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.clientes.models import Cliente as ClienteModel
        m = ClienteModel.objects.filter(pk=cliente_id).first()
        if m:
            m.eliminar(usuario=None)


# ============================================================
# Producto
# ============================================================

class DjangoProductoRepository:
    def obtener_por_id(self, producto_id: int) -> Producto:
        from apps.productos.models import Producto as ProductoModel
        try:
            m = ProductoModel.activos.get(pk=producto_id)
        except ProductoModel.DoesNotExist as exc:
            raise ProductoNoEncontrado(
                f"No existe Producto con id={producto_id}"
            ) from exc
        return modelo_a_producto(m)

    def buscar(
        self, query: str = "", solo_activos: bool = True, limit: int = 50
    ) -> list[Producto]:
        from apps.productos.models import Producto as ProductoModel
        from django.db.models import Q
        qs = ProductoModel.objects.all()
        if solo_activos:
            qs = qs.filter(activo=True)
        if query:
            qs = qs.filter(
                Q(descripcion__icontains=query)
                | Q(codigo__icontains=query)
            )
        return [modelo_a_producto(m) for m in qs[:limit]]

    def guardar(self, producto: Producto) -> Producto:
        from apps.productos.models import Producto as ProductoModel
        if producto.id:
            m = ProductoModel.objects.filter(pk=producto.id).first() or ProductoModel()
        else:
            m = ProductoModel()
        m = producto_a_modelo(producto, m)
        m.save()
        return modelo_a_producto(m)

    def eliminar_soft(self, producto_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.productos.models import Producto as ProductoModel
        m = ProductoModel.objects.filter(pk=producto_id).first()
        if m:
            m.eliminar(usuario=None)


# ============================================================
# Serie
# ============================================================

class DjangoSerieComprobanteRepository:
    SERIE_DEFAULTS = {
        "01": "F001",
        "03": "B001",
        "07": "FC01",
        "08": "FD01",
    }

    def obtener_o_crear(self, empresa_id: int, tipo: str) -> tuple:
        from apps.comprobantes.models import SerieComprobante as SerieModel
        serie_obj, created = SerieModel.objects.select_for_update().get_or_create(
            empresa_id=empresa_id,
            tipo=tipo,
            activo=True,
            defaults={
                "serie": self.SERIE_DEFAULTS.get(tipo, "X001"),
                "correlativo_actual": 0,
            },
        )
        if not created:
            serie_obj.refresh_from_db()
        return modelo_a_serie(serie_obj), created

    def siguiente_correlativo(self, empresa_id: int, tipo: str) -> tuple:
        from apps.comprobantes.models import (
            SerieComprobante as SerieModel,
            Comprobante as CompModel,
        )
        serie_obj, _ = self.obtener_o_crear(empresa_id, tipo)
        max_numero_real = CompModel.objects.filter(
            serie_id=serie_obj.id
        ).aggregate(Max("numero"))["numero__max"] or 0
        siguiente = max(serie_obj.correlativo_actual, max_numero_real) + 1
        serie_obj.correlativo_actual = siguiente
        self.guardar(serie_obj)
        return serie_obj, siguiente

    def guardar(self, serie: SerieComprobante) -> None:
        from apps.comprobantes.models import SerieComprobante as SerieModel
        if serie.id:
            m = SerieModel.objects.filter(pk=serie.id).first()
        else:
            m = None
        m = serie_a_modelo(serie, m)
        m.save()


# ============================================================
# Comprobante
# ============================================================

class DjangoComprobanteRepository:
    def obtener_por_id(self, comprobante_id: int) -> Comprobante:
        from apps.comprobantes.models import Comprobante as CompModel
        try:
            m = CompModel.activos.select_related(
                "cliente", "empresa", "serie"
            ).get(pk=comprobante_id)
        except CompModel.DoesNotExist as exc:
            raise ComprobanteNoEncontrado(
                f"No existe comprobante con id={comprobante_id}"
            ) from exc
        return modelo_a_comprobante(m)

    def listar(
        self,
        empresa_id: Optional[int] = None,
        cliente_id: Optional[int] = None,
        tipo: str = "",
        estado: str = "",
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        ruc_cliente: str = "",
        solo_activos: bool = True,
    ) -> list[Comprobante]:
        from apps.comprobantes.models import Comprobante as CompModel
        qs = CompModel.objects.select_related("cliente", "empresa", "serie")
        if solo_activos:
            qs = qs.filter(activo=True)
        if empresa_id is not None:
            qs = qs.filter(empresa_id=empresa_id)
        if cliente_id is not None:
            qs = qs.filter(cliente_id=cliente_id)
        if tipo:
            qs = qs.filter(tipo=tipo)
        if estado:
            qs = qs.filter(estado=estado)
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)
        if ruc_cliente:
            qs = qs.filter(cliente__num_doc__icontains=ruc_cliente)
        return [modelo_a_comprobante(m) for m in qs.order_by("-fecha", "-creado_en")]

    def guardar(self, comprobante: Comprobante) -> Comprobante:
        from apps.comprobantes.models import Comprobante as CompModel
        from django.db import transaction

        with transaction.atomic():
            if comprobante.id:
                m = CompModel.objects.filter(pk=comprobante.id).first() or CompModel()
            else:
                m = CompModel()
            m = comprobante_a_modelo(comprobante, m)
            m.save()
            # Reemplazar detalles
            from apps.comprobantes.models import DetalleComprobante as DetModel
            DetModel.objects.filter(comprobante_id=m.pk).delete()
            for det in comprobante.detalles:
                dm = detalle_comprobante_a_modelo(det)
                dm.comprobante_id = m.pk
                dm.save()
            guardado = CompModel.objects.select_related(
                "cliente", "empresa", "serie"
            ).get(pk=m.pk)
            return modelo_a_comprobante(guardado)

    def eliminar_soft(self, comprobante_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.comprobantes.models import Comprobante as CompModel
        from django.contrib.auth.models import User
        m = CompModel.objects.filter(pk=comprobante_id).first()
        if m:
            usuario = User.objects.filter(pk=usuario_id).first() if usuario_id else None
            m.eliminar(usuario=usuario)

    def existe_serie_numero(self, serie_id: int, numero: int) -> bool:
        from apps.comprobantes.models import Comprobante as CompModel
        return CompModel.objects.filter(
            serie_id=serie_id, numero=numero, activo=True
        ).exists()


# ============================================================
# Nota de Credito
# ============================================================

class DjangoNotaCreditoRepository:
    def obtener_por_id(self, nota_id: int) -> NotaCredito:
        from apps.notas_credito.models import NotaCredito as NCModel
        try:
            m = NCModel.activos.select_related(
                "comprobante_referencia",
                "comprobante_referencia__cliente",
            ).get(pk=nota_id)
        except NCModel.DoesNotExist as exc:
            raise NotaCreditoNoEncontrada(
                f"No existe NC con id={nota_id}"
            ) from exc
        return modelo_a_nota_credito(m)

    def listar(
        self,
        empresa_id: Optional[int] = None,
        estado: str = "",
        solo_activos: bool = True,
    ) -> list[NotaCredito]:
        from apps.notas_credito.models import NotaCredito as NCModel
        qs = NCModel.objects.select_related(
            "comprobante_referencia",
            "comprobante_referencia__cliente",
        )
        if solo_activos:
            qs = qs.filter(activo=True)
        if estado:
            qs = qs.filter(estado=estado)
        if empresa_id is not None:
            qs = qs.filter(comprobante_referencia__empresa_id=empresa_id)
        return [modelo_a_nota_credito(m) for m in qs.order_by("-fecha", "-creado_en")]

    def guardar(self, nota: NotaCredito) -> NotaCredito:
        from apps.notas_credito.models import NotaCredito as NCModel
        from django.db import transaction

        with transaction.atomic():
            if nota.id:
                m = NCModel.objects.filter(pk=nota.id).first() or NCModel()
            else:
                m = NCModel()
            m = nota_credito_a_modelo(nota, m)
            m.save()
            # Reemplazar detalles
            from apps.notas_credito.models import DetalleNotaCredito as DetModel
            DetModel.objects.filter(nota_credito_id=m.pk).delete()
            for det in nota.detalles:
                dm = detalle_nota_credito_a_modelo(det)
                dm.nota_credito_id = m.pk
                dm.save()
            guardado = NCModel.objects.select_related(
                "comprobante_referencia",
                "comprobante_referencia__cliente",
            ).get(pk=m.pk)
            return modelo_a_nota_credito(guardado)

    def eliminar_soft(self, nota_id: int, usuario_id: Optional[int] = None) -> None:
        from apps.notas_credito.models import NotaCredito as NCModel
        from django.contrib.auth.models import User
        m = NCModel.objects.filter(pk=nota_id).first()
        if m:
            usuario = User.objects.filter(pk=usuario_id).first() if usuario_id else None
            m.eliminar(usuario=usuario)

    def siguiente_numero(self, serie: str) -> int:
        from apps.notas_credito.models import NotaCredito as NCModel
        count = NCModel.objects.filter(serie=serie).count()
        return count + 1


# ============================================================
# Log SUNAT
# ============================================================

class DjangoLogSunatRepository:
    def registrar(
        self,
        comprobante: Comprobante,
        estado_respuesta: str,
        codigo_respuesta: str,
        descripcion: str,
        uuid: str = "",
        cdr_xml: str = "",
    ) -> None:
        from apps.comprobantes.models import LogEnvioSUNAT
        LogEnvioSUNAT.objects.create(
            comprobante_id=comprobante.id,
            estado_respuesta=estado_respuesta,
            codigo_respuesta=codigo_respuesta,
            descripcion=descripcion,
            uuid=uuid or None,
            cdr_xml=cdr_xml or None,
        )

    def obtener_por_comprobante(self, comprobante_id: int) -> list:
        from apps.comprobantes.models import LogEnvioSUNAT
        return list(LogEnvioSUNAT.objects.filter(
            comprobante_id=comprobante_id
        ).order_by("-fecha_envio"))