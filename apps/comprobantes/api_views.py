from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.db.models import Q
from apps.comprobantes.models import Comprobante, SerieComprobante, LogEnvioSUNAT
from apps.comprobantes.serializers import (
    ComprobanteSerializer,
    ComprobanteCreateSerializer,
    LogEnvioSUNATSerializer
)
from apps.sunat_ose.xml_generator import generar_xml_ubl, firmar_xml, crear_zip
import logging

logger = logging.getLogger(__name__)


class ComprobantePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ComprobanteViewSet(viewsets.ModelViewSet):
    queryset = Comprobante.objects.select_related('cliente', 'empresa', 'serie').all()
    serializer_class = ComprobanteSerializer
    pagination_class = ComprobantePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'estado', 'fecha']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        ruc_cliente = self.request.GET.get('ruc_cliente', '')
        if ruc_cliente:
            queryset = queryset.filter(cliente__num_doc__icontains=ruc_cliente)
        
        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        
        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ComprobanteCreateSerializer
        return ComprobanteSerializer

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        serie = request.GET.get('serie', '')
        numero = request.GET.get('numero', '')
        
        if serie and numero:
            try:
                numero_int = int(numero)
                comprobantes = Comprobante.objects.filter(
                    serie__serie=serie,
                    numero=numero_int
                ).select_related('cliente', 'empresa', 'serie')
                
                if comprobantes.exists():
                    data = []
                    for comp in comprobantes:
                        data.append({
                            'id': comp.id,
                            'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                            'cliente': comp.cliente.razon_social,
                            'ruc': comp.cliente.num_doc,
                            'fecha': comp.fecha.strftime('%Y-%m-%d'),
                            'total': float(comp.total),
                            'estado': comp.estado,
                        })
                    return Response(data)
                return Response([], status=status.HTTP_200_OK)
            except ValueError:
                return Response(
                    {'error': 'Número inválido'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {'error': 'Debe proporcionar serie y numero'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['post'])
    def emitir(self, request, pk=None):
        comprobante = self.get_object()
        if comprobante.estado != 'BORRADOR':
            return Response(
                {'error': 'Solo se pueden emitir comprobantes en estado BORRADOR'},
                status=status.HTTP_400_BAD_REQUEST
            )

        comprobante.estado = 'EMITIDO'
        comprobante.save(update_fields=['estado'])
        serializer = self.get_serializer(comprobante)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reenviar(self, request, pk=None):
        comprobante = self.get_object()
        if comprobante.estado != 'RECHAZADO':
            return Response(
                {'error': 'Solo se pueden reenviar comprobantes en estado RECHAZADO'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            xml_content = generar_xml_ubl(comprobante)
            xml_firmado = firmar_xml(xml_content, empresa_id=comprobante.empresa_id)

            comprobante.xml_firmado = xml_firmado.decode('utf-8') if isinstance(xml_firmado, bytes) else xml_firmado
            comprobante.estado = 'ENVIADO'
            comprobante.save(update_fields=['xml_firmado', 'estado'])

            logger.info(f"Comprobante {comprobante} reenviado exitosamente")
            serializer = self.get_serializer(comprobante)
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error reenviando comprobante {comprobante}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        comprobante = self.get_object()
        from django.http import HttpResponse
        from weasyprint import HTML
        from django.template.loader import render_to_string

        html_string = render_to_string('comprobantes/pdf_template.html', {
            'comprobante': comprobante,
            'detalles': comprobante.detalles.all(),
        })

        html = HTML(string=html_string)
        pdf_content = html.write_pdf()

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}.pdf"'
        return response

    @action(detail=True, methods=['get'])
    def xml(self, request, pk=None):
        comprobante = self.get_object()
        if not comprobante.xml_firmado:
            return Response(
                {'error': 'Este comprobante no tiene XML generado'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = HttpResponse(comprobante.xml_firmado.encode('utf-8'), content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}"'
        return response

    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        comprobante = self.get_object()
        serializer = self.get_serializer(comprobante)
        return Response(serializer.data)


class LogEnvioSUNATViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEnvioSUNAT.objects.select_related('comprobante').all()
    serializer_class = LogEnvioSUNATSerializer
    pagination_class = ComprobantePagination
    filterset_fields = ['comprobante', 'estado_respuesta']