"""
Service Layer para el módulo de Reportes.
"""

from datetime import datetime
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from apps.comprobantes.models import Comprobante


class ReporteService:
    """Lógica de negocio para generación de reportes."""

    @staticmethod
    def ventas_por_periodo(mes: int, anio: int) -> dict:
        """
        Genera el reporte de ventas (libro de ventas simplificado) para un período.

        Returns:
            dict con data (lista de comprobantes) y resumen
        """
        comprobantes = Comprobante.objects.filter(
            fecha__month=mes,
            fecha__year=anio,
            estado='ACEPTADO'
        ).select_related('cliente', 'empresa', 'serie')

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
            'total_facturas': sum(1 for c in data if c['tipo'] == '01'),
            'total_boletas': sum(1 for c in data if c['tipo'] == '03'),
            'total_nc': sum(1 for c in data if c['tipo'] == '07'),
            'subtotal': sum(c['subtotal'] for c in data),
            'igv': sum(c['igv'] for c in data),
            'total': sum(c['total'] for c in data),
        }

        return {
            'data': data,
            'resumen': resumen,
            'comprobantes': comprobantes,
            'periodo': {'mes': mes, 'anio': anio},
        }

    @staticmethod
    def dashboard_resumen() -> dict:
        """
        Genera el resumen del dashboard: estadísticas del mes actual.

        Returns:
            dict con conteos, montos, alertas y datos para gráficos
        """
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
        total_ventas = sum(
            float(c.total) for c in comprobantes_mes.filter(estado='ACEPTADO')
        )

        rechazados = comprobantes_mes.filter(estado='RECHAZADO')[:10]
        ultimos = comprobantes_mes.order_by('-fecha', '-creado_en')[:10]

        # Datos para gráficos
        ventas_por_mes = Comprobante.objects.filter(estado='ACEPTADO') \
            .annotate(month=TruncMonth('fecha')) \
            .values('month') \
            .annotate(total=Sum('total'), count=Count('id')) \
            .order_by('month')

        chart_labels = [v['month'].strftime('%b') for v in ventas_por_mes]
        chart_ventas = [float(v['total']) for v in ventas_por_mes]
        chart_counts = [v['count'] for v in ventas_por_mes]

        return {
            'facturas_mes': facturas_mes,
            'boletas_mes': boletas_mes,
            'notas_credito_mes': notas_credito_mes,
            'aceptadas_mes': aceptadas_mes,
            'rechazadas_mes': rechazadas_mes,
            'total_ventas': f"{total_ventas:.2f}",
            'comprobantes_rechazados': rechazados,
            'ultimos_comprobantes': ultimos,
            'total_comprobantes_mes': comprobantes_mes.count(),
            'chart_labels': chart_labels,
            'chart_ventas': chart_ventas,
            'chart_counts': chart_counts,
        }
