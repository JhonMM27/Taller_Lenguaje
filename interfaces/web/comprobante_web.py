"""
Vistas web (templates) del modulo de comprobantes.

Estas vistas son adaptadores delgados: renderizan templates y
delegan toda la logica al servicio de dominio.
"""
from __future__ import annotations

from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse

from apps.clientes.models import Cliente
from apps.comprobantes.models import (
    Comprobante,
    DetalleComprobante,
    SerieComprobante,
)
from apps.empresas.models import Empresa
from apps.productos.models import Producto
from dominio.excepciones import (
    ClienteNoEncontrado,
    EmpresaNoEncontrada,
    EstadoInvalido,
    TipoDocumentoInvalido,
)
from interfaces.container import get_comprobante_service


@login_required
def lista_comprobantes(request):
    """Vista delgada: usa el servicio de dominio para listar."""
    servicio = get_comprobante_service()
    empresa_id = request.user.perfil.empresa_id if (
        hasattr(request.user, "perfil") and request.user.perfil.empresa_id
    ) else None

    try:
        comprobantes = servicio.listar(
            empresa_id=empresa_id,
            tipo=request.GET.get("tipo", ""),
            estado=request.GET.get("estado", ""),
        )
    except Exception:
        # Fallback a query directa si el servicio falla
        comprobantes = Comprobante.activos.select_related(
            "cliente", "empresa", "serie"
        ).all()

    paginator = Paginator(comprobantes, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "comprobantes/lista.html", {
        "comprobantes": page_obj,
        "tipos": SerieComprobante.TIPO_CHOICES,
        "estados": Comprobante.ESTADO_CHOICES,
        "empresas": Empresa.objects.all(),
        "clientes": Cliente.objects.all(),
        "productos": Producto.objects.all(),
        "today": datetime.now().strftime("%Y-%m-%d"),
    })


@login_required
def crear_comprobante(request):
    """Vista delgada: delega al ComprobanteService.crear()."""
    if request.method == "POST":
        detalles_data = []
        producto_ids = request.POST.getlist("producto_id")
        cantidades = request.POST.getlist("cantidad")
        precios = request.POST.getlist("precio_unitario")

        for i, producto_id in enumerate(producto_ids):
            if not producto_id or not producto_id.strip():
                continue
            detalles_data.append({
                "producto_id": producto_id,
                "cantidad": cantidades[i] if i < len(cantidades) else 1,
                "precio_unitario": precios[i] if i < len(precios) else 0,
            })

        if not detalles_data:
            return render(request, "comprobantes/crear.html", {
                "errors": {"detalles": ["Debe seleccionar al menos un producto"]},
                "empresas": Empresa.objects.all(),
                "clientes": Cliente.objects.all(),
                "productos": Producto.objects.all(),
                "today": datetime.now().strftime("%Y-%m-%d"),
            })

        try:
            servicio = get_comprobante_service()
            comprobante = servicio.crear(
                empresa_id=int(request.POST.get("empresa_id")),
                cliente_id=int(request.POST.get("cliente_id")),
                fecha=request.POST.get("fecha"),
                tipo=request.POST.get("tipo"),
                detalles_data=detalles_data,
                creado_por_id=request.user.id if request.user.is_authenticated else None,
            )
            messages.success(
                request,
                f"Comprobante {comprobante.numero_formateado} creado exitosamente",
            )
            return redirect("comprobantes:lista")
        except (TipoDocumentoInvalido, EstadoInvalido,
                ClienteNoEncontrado, EmpresaNoEncontrada) as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, str(e))

    empresas = Empresa.objects.all()
    return render(request, "comprobantes/crear.html", {
        "empresas": empresas,
        "clientes": Cliente.objects.all(),
        "productos": Producto.objects.all(),
        "today": datetime.now().strftime("%Y-%m-%d"),
        "empresa_default": empresas.first() if empresas.count() == 1 else None,
    })


@login_required
def detalle_comprobante(request, pk):
    comprobante = get_object_or_404(
        Comprobante.objects.select_related("cliente", "empresa", "serie"),
        pk=pk,
    )
    return render(request, "comprobantes/detalle.html", {
        "comprobante": comprobante,
    })


@login_required
def emitir_comprobante(request, pk):
    try:
        servicio = get_comprobante_service()
        servicio.emitir(comprobante_id=int(pk))
        messages.success(request, "Comprobante emitido exitosamente")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("comprobantes:detalle", pk=pk)


@login_required
def reenviar_comprobante(request, pk):
    try:
        servicio = get_comprobante_service()
        servicio.reenviar(comprobante_id=int(pk))
        messages.success(request, "Comprobante reenviado exitosamente")
    except Exception as e:
        messages.error(request, str(e))
    return redirect("comprobantes:detalle", pk=pk)