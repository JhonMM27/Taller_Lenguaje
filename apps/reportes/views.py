from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
from apps.comprobantes.models import Comprobante
from datetime import datetime


@method_decorator(csrf_exempt, name='dispatch')
class ReporteVentasPeriodoView(View):
    def get(self, request):
        mes = request.GET.get('mes')
        anio = request.GET.get('anio')

        if not mes or not anio:
            mes = datetime.now().month
            anio = datetime.now().year

        mes = int(mes)
        anio = int(anio)

        comprobantes = Comprobante.objects.filter(
            fecha__month=mes,
            fecha__year=anio,
            estado='ACEPTADO'
        ).select_related('cliente', 'empresa')

        data = []
        for comp in comprobantes:
            data.append({
                'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                'fecha': comp.fecha.strftime('%Y-%m-%d'),
                'tipo': comp.tipo,
                'tipo_display': comp.get_tipo_display(),
                'cliente': comp.cliente.razon_social,
                'ruc': comp.cliente.num_doc,
                'subtotal': float(comp.subtotal),
                'igv': float(comp.igv),
                'total': float(comp.total),
            })

        resumen = {
            'total_facturas': 0,
            'total_boletas': 0,
            'subtotal': 0,
            'igv': 0,
            'total': 0,
        }

        for comp in data:
            if comp['tipo'] == '01':
                resumen['total_facturas'] += 1
            elif comp['tipo'] == '03':
                resumen['total_boletas'] += 1
            resumen['subtotal'] += comp['subtotal']
            resumen['igv'] += comp['igv']
            resumen['total'] += comp['total']

        return JsonResponse({
            'data': data,
            'resumen': resumen,
            'periodo': {'mes': mes, 'anio': anio}
        })


@method_decorator(csrf_exempt, name='dispatch')
class DashboardView(View):
    def get(self, request):
        hoy = datetime.now()
        mes_actual = hoy.month
        anio_actual = hoy.year

        comprobantes_mes = Comprobante.objects.filter(
            fecha__month=mes_actual,
            fecha__year=anio_actual
        ).select_related('cliente', 'empresa')

        total_facturas = comprobantes_mes.filter(tipo='01').count()
        total_boletas = comprobantes_mes.filter(tipo='03').count()

        aceptados = comprobantes_mes.filter(estado='ACEPTADO')
        rechazados = comprobantes_mes.filter(estado='RECHAZADO')

        rechazados_lista = []
        for comp in rechazados:
            rechazados_lista.append({
                'id': comp.id,
                'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                'cliente': comp.cliente.razon_social,
                'total': float(comp.total),
            })

        resumen = {
            'total_facturas': total_facturas,
            'total_boletas': total_boletas,
            'total_aceptados': aceptados.count(),
            'total_rechazados': rechazados.count(),
            'monto_total': float(sum(c.total for c in aceptados)),
            'rechazados_pendientes': rechazados_lista,
        }

        return JsonResponse(resumen)


@login_required
def reporte_ventas(request):
    mes = request.GET.get('mes')
    anio = request.GET.get('anio')
    formato = request.GET.get('formato', 'html')

    if not mes:
        mes = datetime.now().month
    if not anio:
        anio = datetime.now().year

    mes = int(mes)
    anio = int(anio)

    comprobantes = Comprobante.objects.filter(
        fecha__month=mes,
        fecha__year=anio,
        estado='ACEPTADO'
    ).select_related('cliente', 'empresa', 'serie')

    total_facturas = comprobantes.filter(tipo='01').count()
    total_boletas = comprobantes.filter(tipo='03').count()
    subtotal_total = sum(float(c.subtotal) for c in comprobantes)
    igv_total = sum(float(c.igv) for c in comprobantes)
    total_total = sum(float(c.total) for c in comprobantes)

    resumen = {
        'total_facturas': total_facturas,
        'total_boletas': total_boletas,
        'subtotal': subtotal_total,
        'igv': igv_total,
        'total': total_total,
    }

    meses = [
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'),
        ('4', 'Abril'), ('5', 'Mayo'), ('6', 'Junio'),
        ('7', 'Julio'), ('8', 'Agosto'), ('9', 'Septiembre'),
        ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ]

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

    return render(request, 'reportes/ventas.html', {
        'comprobantes': comprobantes,
        'resumen': resumen,
        'mes_actual': mes,
        'anio_actual': anio,
        'meses': meses,
    })


@login_required
def dashboard(request):
    hoy = datetime.now()
    mes_actual = hoy.month
    anio_actual = hoy.year

    comprobantes_mes = Comprobante.objects.filter(
        fecha__month=mes_actual,
        fecha__year=anio_actual
    ).select_related('cliente', 'empresa', 'serie')

    facturas_mes = comprobantes_mes.filter(tipo='01').count()
    boletas_mes = comprobantes_mes.filter(tipo='03').count()
    notas_credito_mes = comprobantes_mes.filter(tipo='07').count()
    
    aceptadas_mes = comprobantes_mes.filter(estado='ACEPTADO').count()
    rechazadas_mes = comprobantes_mes.filter(estado='RECHAZADO').count()
    total_ventas = sum(float(c.total) for c in comprobantes_mes.filter(estado='ACEPTADO'))

    rechazados = comprobantes_mes.filter(estado='RECHAZADO')[:10]
    ultimos = comprobantes_mes.order_by('-fecha', '-created_at')[:10]

    # Datos para el gráfico de barras (últimos 6 meses)
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    
    ventas_por_mes = Comprobante.objects.filter(estado='ACEPTADO') \
        .annotate(month=TruncMonth('fecha')) \
        .values('month') \
        .annotate(total=Sum('total'), count=Count('id')) \
        .order_by('month')
    
    chart_labels = []
    chart_ventas = []
    chart_counts = []
    
    for v in ventas_por_mes:
        chart_labels.append(v['month'].strftime('%b'))
        chart_ventas.append(float(v['total']))
        chart_counts.append(v['count'])

    from apps.clientes.models import Cliente
    from apps.productos.models import Producto, CategoriaProducto
    
    return render(request, 'dashboard.html', {
        'facturas_mes': facturas_mes,
        'aceptadas_mes': aceptadas_mes,
        'rechazadas_mes': rechazadas_mes,
        'total_ventas': f"{total_ventas:.2f}",
        'comprobantes_rechazados': rechazados,
        'ultimos_comprobantes': ultimos,
        'total_clientes': Cliente.objects.count(),
        'total_productos': Producto.objects.count(),
        'categorias': CategoriaProducto.objects.filter(activa=True),
        'chart_labels': chart_labels,
        'chart_ventas': chart_ventas,
        'chart_counts': chart_counts,
        'total_comprobantes_mes': comprobantes_mes.count(),
        'boletas_mes': boletas_mes,
        'notas_credito_mes': notas_credito_mes,
        'today': hoy.strftime('%Y-%m-%d'),
    })