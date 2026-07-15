"""
API Views del módulo de Comprobantes.

Views delgadas: delegan toda lógica al ComprobanteService.
Capturan excepciones de dominio con handlers específicos.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from apps.comprobantes.serializers import (
    ComprobanteSerializer,
    ComprobanteCreateSerializer,
    LogEnvioSUNATSerializer,
)
from apps.comprobantes.services import ComprobanteService
from apps.core.exceptions import (
    AppError, ReglaNegocioViolada, RecursoNoEncontrado,
    TipoDocumentoInvalido, EstadoInvalido, ComprobanteNoAnulable,
)

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
        queryset = Comprobante.activos.select_related('cliente', 'empresa', 'serie').all()
        
        user = self.request.user
        if user and user.is_authenticated:
            try:
                perfil = user.perfil
                if perfil.rol != 'ADMIN' and perfil.empresa:
                    queryset = queryset.filter(empresa=perfil.empresa)
            except AttributeError:
                pass
        
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

    def create(self, request, *args, **kwargs):
        """View delgada: delega al ComprobanteService.crear()."""
        try:
            comprobante = ComprobanteService.crear(
                data=request.data,
                usuario=request.user,
            )
            return Response(
                ComprobanteSerializer(comprobante).data,
                status=status.HTTP_201_CREATED,
            )
        except TipoDocumentoInvalido as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ReglaNegocioViolada as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
                
                data = [
                    {
                        'id': comp.id,
                        'numero': f"{comp.serie.serie}-{comp.numero:08d}",
                        'cliente': comp.cliente.razon_social,
                        'ruc': comp.cliente.num_doc,
                        'fecha': comp.fecha.strftime('%Y-%m-%d'),
                        'total': float(comp.total),
                        'estado': comp.estado,
                    }
                    for comp in comprobantes
                ]
                return Response(data)
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
        """View delgada: delega al ComprobanteService.emitir()."""
        try:
            comprobante = ComprobanteService.emitir(pk)
            serializer = self.get_serializer(comprobante)
            return Response(serializer.data)
        except EstadoInvalido as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def reenviar(self, request, pk=None):
        """View delgada: delega al ComprobanteService.reenviar()."""
        try:
            comprobante = ComprobanteService.reenviar(pk)
            logger.info(f"Comprobante {comprobante} reenviado exitosamente")
            serializer = self.get_serializer(comprobante)
            return Response(serializer.data)
        except EstadoInvalido as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except AppError as e:
            logger.error(f"Error reenviando comprobante {pk}: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        comprobante = self.get_object()
        from django.http import HttpResponse
        # pyrefly: ignore [missing-import]
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

        from django.http import HttpResponse
        response = HttpResponse(comprobante.xml_firmado.encode('utf-8'), content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="{comprobante.nombre_xml}"'
        return response

    @action(detail=True, methods=['get'])
    def detalle_completo(self, request, pk=None):
        comprobante = self.get_object()
        serializer = self.get_serializer(comprobante)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def eliminar_soft(self, request, pk=None):
        """Soft delete — comprobantes ACEPTADOS no se pueden eliminar."""
        try:
            ComprobanteService.eliminar(pk, usuario=request.user)
            return Response({'status': 'eliminado'}, status=status.HTTP_200_OK)
        except ComprobanteNoAnulable as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)


class LogEnvioSUNATViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogEnvioSUNAT.objects.select_related('comprobante').all()
    serializer_class = LogEnvioSUNATSerializer
    pagination_class = ComprobantePagination
    filterset_fields = ['comprobante', 'estado_respuesta']