"""
Views del módulo de Reportes.

Views delgadas: delegan al ReporteService.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from datetime import datetime

from apps.reportes.services import ReporteService
from apps.comprobantes.models import Comprobante


@method_decorator(csrf_exempt, name='dispatch')
class ReporteVentasPeriodoView(View):
    """API: Reporte de ventas por período — delega al ReporteService."""

    def get(self, request):
        mes = request.GET.get('mes')
        anio = request.GET.get('anio')

        if not mes or not anio:
            mes = datetime.now().month
            anio = datetime.now().year

        resultado = ReporteService.ventas_por_periodo(int(mes), int(anio))
        return JsonResponse({
            'data': resultado['data'],
            'resumen': resultado['resumen'],
            'periodo': resultado['periodo'],
        })


@method_decorator(csrf_exempt, name='dispatch')
class DashboardView(View):
    """API: Dashboard — delega al ReporteService."""

    def get(self, request):
        resumen = ReporteService.dashboard_resumen()

        # Serializar rechazados para JSON
        rechazados_lista = []
        for comp in resumen.get('comprobantes_rechazados', []):
            rechazados_lista.append({
                'id': comp.id,
                'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                'cliente': comp.cliente.razon_social,
                'total': float(comp.total),
            })

        return JsonResponse({
            'total_facturas': resumen['facturas_mes'],
            'total_boletas': resumen.get('boletas_mes', 0),
            'total_aceptados': resumen['aceptadas_mes'],
            'total_rechazados': resumen['rechazadas_mes'],
            'monto_total': float(resumen['total_ventas'].replace(',', '')) if isinstance(resumen['total_ventas'], str) else float(resumen['total_ventas']),
            'rechazados_pendientes': rechazados_lista,
        })


@login_required
def reporte_ventas(request):
    """Vista web: Libro de ventas — delega al ReporteService."""
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    formato = request.GET.get('formato', 'html')

    if not mes:
        mes = datetime.now().month
    if not anio:
        anio = datetime.now().year

    mes = int(mes)
    anio = int(anio)

    resultado = ReporteService.ventas_por_periodo(mes, anio)
    comprobantes = resultado['comprobantes']
    resumen = resultado['resumen']

    meses = [
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
        ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
        ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ]

    # Exportar a Excel si se solicita
    if formato == 'excel':
        data = []
        for comp in comprobantes:
            data.append({
                'Numero': f"{comp.serie.serie}-{comp.numero:08d}",
                'Fecha': comp.fecha.strftime('%Y-%m-%d'),
                'Tipo': comp.get_tipo_display(),
                'Cliente': comp.cliente.razon_social,
                'RUC': comp.cliente.num_doc,
                'Subtotal': float(comp.subtotal),
                'IGV': float(comp.igv),
                'Total': float(comp.total),
            })
        df = pd.DataFrame(data)
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=reporte_ventas_{mes}_{anio}.xlsx'
        df.to_excel(response, index=False)
        return response

    # Datos para gráficos
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth

    ventas_por_dia = comprobantes.values('fecha').annotate(
        total=Sum('total'), count=Count('id')
    ).order_by('fecha')

    chart_dia_labels = [v['fecha'].strftime('%d/%m') for v in ventas_por_dia]
    chart_dia_ventas = [float(v['total']) for v in ventas_por_dia]

    ventas_por_tipo = comprobantes.values('tipo').annotate(
        total=Sum('total'), count=Count('id')
    ).order_by('tipo')

    chart_tipo_labels = []
    chart_tipo_ventas = []
    chart_tipo_counts = []
    for v in ventas_por_tipo:
        if v['tipo'] == '01':
            label = 'Facturas'
        elif v['tipo'] == '03':
            label = 'Boletas'
        elif v['tipo'] == '07':
            label = 'Notas Crédito'
        else:
            label = v['tipo']
        chart_tipo_labels.append(label)
        chart_tipo_ventas.append(float(v['total']))
        chart_tipo_counts.append(v['count'])

    ventas_por_categoria = comprobantes.values(
        'detalles__producto__categoria__nombre'
    ).annotate(total=Sum('total')).order_by('-total')

    chart_cat_labels = []
    chart_cat_ventas = []
    for v in ventas_por_categoria:
        cat = v['detalles__producto__categoria__nombre'] or 'Sin categoría'
        chart_cat_labels.append(cat)
        chart_cat_ventas.append(float(v['total']))

    ventas_mensuales_historico = Comprobante.objects.filter(
        estado='ACEPTADO'
    ).annotate(mes=TruncMonth('fecha')).values('mes').annotate(
        total=Sum('total'), count=Count('id')
    ).order_by('mes')

    chart_hist_labels = [v['mes'].strftime('%b %Y') for v in ventas_mensuales_historico]
    chart_hist_ventas = [float(v['total']) for v in ventas_mensuales_historico]

    n = comprobantes.count()
    saldo_promedio = resumen['total'] / n if n > 0 else 0

    return render(request, 'reportes/ventas.html', {
        'comprobantes': comprobantes,
        'resumen': resumen,
        'mes_actual': mes,
        'anio_actual': anio,
        'meses': meses,
        'chart_dia_labels': chart_dia_labels,
        'chart_dia_ventas': chart_dia_ventas,
        'chart_tipo_labels': chart_tipo_labels,
        'chart_tipo_ventas': chart_tipo_ventas,
        'chart_tipo_counts': chart_tipo_counts,
        'chart_cat_labels': chart_cat_labels,
        'chart_cat_ventas': chart_cat_ventas,
        'chart_hist_labels': chart_hist_labels,
        'chart_hist_ventas': chart_hist_ventas,
        'saldo_promedio': round(saldo_promedio, 2),
    })


@login_required
def dashboard(request):
    """Vista web: Dashboard — delega al ReporteService."""
    resumen = ReporteService.dashboard_resumen()

    from apps.clientes.models import Cliente
    from apps.productos.models import Producto, CategoriaProducto

    resumen['total_clientes'] = Cliente.objects.count()
    resumen['total_productos'] = Producto.objects.count()
    resumen['categorias'] = CategoriaProducto.activos.all()
    resumen['today'] = datetime.now().strftime('%Y-%m-%d')

    return render(request, 'dashboard.html', resumen)