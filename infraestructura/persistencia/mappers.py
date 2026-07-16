"""
Mappers entre entidades de dominio (dataclasses) y modelos Django (ORM).

Funciones puras que convierten en ambas direcciones. Esto aísla el dominio
de Django y permite que las entidades sean Python puro.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from dominio.entidades import (
    Cliente,
    Producto,
    Comprobante,
    DetalleComprobante,
    NotaCredito,
    DetalleNotaCredito,
    SerieComprobante,
    Empresa,
    CategoriaProducto,
)


# ============================================================
# Empresa
# ============================================================

def empresa_a_modelo(ent: Empresa, modelo=None):
    """Convierte Empresa (dominio) -> Empresa (Django ORM)."""
    from apps.empresas.models import Empresa as EmpresaModel
    obj = modelo or EmpresaModel()
    obj.ruc = ent.ruc
    obj.razon_social = ent.razon_social
    obj.nombre_comercial = ent.nombre_comercial
    obj.direccion = ent.direccion
    obj.telefono = ent.telefono
    obj.email = ent.email
    obj.regimen_tributario = ent.regimen_tributario
    obj.codigo = ent.codigo
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_empresa(modelo) -> Empresa:
    return Empresa(
        id=modelo.pk,
        ruc=modelo.ruc,
        razon_social=modelo.razon_social,
        nombre_comercial=modelo.nombre_comercial,
        direccion=modelo.direccion,
        telefono=modelo.telefono,
        email=modelo.email,
        regimen_tributario=modelo.regimen_tributario or "GENERAL",
        logo=str(modelo.logo) if modelo.logo else None,
        codigo=modelo.codigo,
        activo=modelo.activo,
    )


# ============================================================
# Cliente
# ============================================================

def cliente_a_modelo(ent: Cliente, modelo=None):
    from apps.clientes.models import Cliente as ClienteModel
    obj = modelo or ClienteModel()
    obj.tipo_doc = ent.tipo_doc
    obj.num_doc = ent.num_doc
    obj.razon_social = ent.razon_social
    obj.codigo = ent.codigo
    obj.direccion = ent.direccion
    obj.telefono = ent.telefono
    obj.email = ent.email
    obj.ubigeo = ent.ubigeo
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_cliente(modelo) -> Cliente:
    return Cliente(
        id=modelo.pk,
        tipo_doc=modelo.tipo_doc,
        num_doc=modelo.num_doc,
        razon_social=modelo.razon_social,
        codigo=modelo.codigo,
        direccion=modelo.direccion,
        telefono=modelo.telefono,
        email=modelo.email,
        ubigeo=modelo.ubigeo,
        activo=modelo.activo,
    )


# ============================================================
# Producto
# ============================================================

def producto_a_modelo(ent: Producto, modelo=None):
    from apps.productos.models import Producto as ProductoModel
    obj = modelo or ProductoModel()
    obj.descripcion = ent.descripcion
    obj.unidad_medida = ent.unidad_medida
    obj.precio_unitario = ent.precio_unitario
    obj.afecto_igv = ent.afecto_igv
    obj.cod_tipo_afectacion = ent.cod_tipo_afectacion
    obj.codigo = ent.codigo
    obj.tipo_operacion = ent.tipo_operacion
    if ent.categoria_id is not None:
        obj.categoria_id = ent.categoria_id
    elif ent.categoria is not None and ent.categoria.id is not None:
        obj.categoria_id = ent.categoria.id
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_producto(modelo) -> Producto:
    return Producto(
        id=modelo.pk,
        descripcion=modelo.descripcion,
        precio_unitario=modelo.precio_unitario,
        unidad_medida=modelo.unidad_medida or "NIU",
        afecto_igv=modelo.afecto_igv,
        cod_tipo_afectacion=modelo.cod_tipo_afectacion or "10",
        codigo=modelo.codigo,
        tipo_operacion=modelo.tipo_operacion or "GRAVADA",
        categoria_id=modelo.categoria_id,
        activo=modelo.activo,
    )


# ============================================================
# SerieComprobante
# ============================================================

def serie_a_modelo(ent: SerieComprobante, modelo=None):
    from apps.comprobantes.models import SerieComprobante as SerieModel
    obj = modelo or SerieModel()
    obj.empresa_id = ent.empresa_id
    obj.tipo = ent.tipo
    obj.serie = ent.serie
    obj.correlativo_actual = ent.correlativo_actual
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_serie(modelo) -> SerieComprobante:
    return SerieComprobante(
        id=modelo.pk,
        empresa_id=modelo.empresa_id,
        tipo=modelo.tipo,
        serie=modelo.serie,
        correlativo_actual=modelo.correlativo_actual,
        activo=modelo.activo,
    )


# ============================================================
# DetalleComprobante
# ============================================================

def detalle_comprobante_a_modelo(ent: DetalleComprobante, modelo=None):
    from apps.comprobantes.models import DetalleComprobante as DetModel
    obj = modelo or DetModel()
    obj.producto_id = ent.producto_id
    obj.cantidad = ent.cantidad
    obj.precio_unitario = ent.precio_unitario
    obj.descuento = ent.descuento
    obj.afecto_igv = ent.afecto_igv
    obj.cod_tipo_afectacion = ent.cod_tipo_afectacion
    obj.igv_linea = ent.igv_linea
    obj.subtotal = ent.subtotal
    if ent.id is not None:
        obj.pk = ent.id
    return obj


def modelo_a_detalle_comprobante(modelo) -> DetalleComprobante:
    return DetalleComprobante(
        id=modelo.pk,
        producto_id=modelo.producto_id,
        cantidad=modelo.cantidad,
        precio_unitario=modelo.precio_unitario,
        descuento=modelo.descuento or Decimal("0"),
        afecto_igv=modelo.afecto_igv,
        cod_tipo_afectacion=modelo.cod_tipo_afectacion or "10",
        igv_linea=modelo.igv_linea or Decimal("0"),
        subtotal=modelo.subtotal or Decimal("0"),
    )


# ============================================================
# Comprobante
# ============================================================

def comprobante_a_modelo(ent: Comprobante, modelo=None):
    from apps.comprobantes.models import Comprobante as CompModel
    obj = modelo or CompModel()
    obj.empresa_id = ent.empresa_id
    obj.cliente_id = ent.cliente_id
    obj.serie_id = ent.serie_id
    obj.numero = ent.numero
    obj.fecha = ent.fecha
    obj.tipo = ent.tipo
    obj.estado = ent.estado
    obj.subtotal = ent.subtotal
    obj.igv = ent.igv
    obj.total = ent.total
    obj.xml_firmado = ent.xml_firmado
    obj.sunat_ticket = ent.sunat_ticket
    obj.zip_path = ent.zip_path
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_comprobante(modelo) -> Comprobante:
    return Comprobante(
        id=modelo.pk,
        empresa_id=modelo.empresa_id,
        cliente_id=modelo.cliente_id,
        serie_id=modelo.serie_id,
        numero=modelo.numero,
        fecha=modelo.fecha,
        tipo=modelo.tipo,
        estado=modelo.estado,
        subtotal=modelo.subtotal or Decimal("0"),
        igv=modelo.igv or Decimal("0"),
        total=modelo.total or Decimal("0"),
        xml_firmado=modelo.xml_firmado,
        zip_path=modelo.zip_path,
        sunat_ticket=modelo.sunat_ticket,
        activo=modelo.activo,
    )


# ============================================================
# DetalleNotaCredito
# ============================================================

def detalle_nota_credito_a_modelo(ent: DetalleNotaCredito, modelo=None):
    from apps.notas_credito.models import DetalleNotaCredito as DetModel
    obj = modelo or DetModel()
    obj.producto_id = ent.producto_id
    obj.cantidad = ent.cantidad
    obj.precio_unitario = ent.precio_unitario
    obj.descuento = ent.descuento
    obj.afecto_igv = ent.afecto_igv
    obj.cod_tipo_afectacion = ent.cod_tipo_afectacion
    obj.igv_linea = ent.igv_linea
    obj.subtotal = ent.subtotal
    if ent.id is not None:
        obj.pk = ent.id
    return obj


def modelo_a_detalle_nota_credito(modelo) -> DetalleNotaCredito:
    return DetalleNotaCredito(
        id=modelo.pk,
        nota_credito_id=modelo.nota_credito_id,
        producto_id=modelo.producto_id,
        cantidad=modelo.cantidad,
        precio_unitario=modelo.precio_unitario,
        descuento=modelo.descuento or Decimal("0"),
        afecto_igv=modelo.afecto_igv,
        cod_tipo_afectacion=modelo.cod_tipo_afectacion or "10",
        igv_linea=modelo.igv_linea or Decimal("0"),
        subtotal=modelo.subtotal or Decimal("0"),
    )


# ============================================================
# NotaCredito
# ============================================================

def nota_credito_a_modelo(ent: NotaCredito, modelo=None):
    from apps.notas_credito.models import NotaCredito as NCModel
    obj = modelo or NCModel()
    obj.comprobante_referencia_id = ent.comprobante_referencia_id
    obj.serie = ent.serie
    obj.numero = ent.numero
    obj.fecha = ent.fecha
    obj.tipo_nc = ent.tipo_nc
    obj.tipo_nota = ent.tipo_nota
    obj.op_gravada = ent.op_gravada
    obj.igv = ent.igv
    obj.importe = ent.importe
    obj.descripcion = ent.descripcion
    obj.estado = ent.estado
    obj.xml_firmado = ent.xml_firmado
    obj.sunat_ticket = ent.sunat_ticket
    obj.cdr_xml = ent.cdr_xml
    obj.mensaje_sunat = ent.mensaje_sunat
    if ent.id is not None:
        obj.pk = ent.id
    if ent.activo is not None:
        obj.activo = ent.activo
    return obj


def modelo_a_nota_credito(modelo) -> NotaCredito:
    return NotaCredito(
        id=modelo.pk,
        comprobante_referencia_id=modelo.comprobante_referencia_id,
        serie=modelo.serie,
        numero=modelo.numero,
        fecha=modelo.fecha,
        tipo_nc=modelo.tipo_nc,
        tipo_nota=modelo.tipo_nota,
        op_gravada=modelo.op_gravada or Decimal("0"),
        igv=modelo.igv or Decimal("0"),
        importe=modelo.importe or Decimal("0"),
        descripcion=modelo.descripcion or "",
        estado=modelo.estado,
        xml_firmado=modelo.xml_firmado,
        sunat_ticket=modelo.sunat_ticket,
        cdr_xml=modelo.cdr_xml,
        mensaje_sunat=modelo.mensaje_sunat,
        activo=modelo.activo,
    )