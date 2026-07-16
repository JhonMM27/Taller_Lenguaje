"""
ViewSets de DRF para comprobantes.

Views delgadas: reciben request, llaman al servicio de dominio via DI
y devuelven la respuesta.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from apps.comprobantes.models import Comprobante, LogEnvioSUNAT
from dominio.excepciones import (
    AccesoNoAutorizado,
    ComprobanteNoEncontrado,
    DomainError,
    EstadoInvalido,
)
from interfaces.container import (
    get_comprobante_service,
    get_sunat_service,
)
from interfaces.api.serializers import (
    ComprobanteCreateSerializer,
    ComprobanteReenviarSerializer,
    ComprobanteSerializer,
    ComprobanteEdicionSerializer,
    LogEnvioSUNATSerializer,
)

logger = logging.getLogger(__name__)


class ComprobantePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ComprobanteViewSet(viewsets.ModelViewSet):
    """ViewSet delgado. Solo delega al servicio de dominio."""

    queryset = Comprobante.objects.all()
    serializer_class = ComprobanteSerializer
    pagination_class = ComprobantePagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo', 'estado', 'fecha']

    def get_queryset(self):
        qs = Comprobante.activos.select_related(
            'cliente', 'empresa', 'serie'
        ).all()
        user = self.request.user
        if user and user.is_authenticated:
            try:
                perfil = user.perfil
                if perfil.rol != 'ADMIN' and perfil.empresa:
                    qs = qs.filter(empresa=perfil.empresa)
            except AttributeError:
                pass

        ruc_cliente = self.request.GET.get('ruc_cliente', '')
        if ruc_cliente:
            qs = qs.filter(cliente__num_doc__icontains=ruc_cliente)

        fecha_desde = self.request.GET.get('fecha_desde', '')
        if fecha_desde:
            qs = qs.filter(fecha__gte=fecha_desde)

        fecha_hasta = self.request.GET.get('fecha_hasta', '')
        if fecha_hasta:
            qs = qs.filter(fecha__lte=fecha_hasta)

        return qs.order_by('-fecha', '-creado_en')

    def get_serializer_class(self):
        if self.action == 'create':
            return ComprobanteCreateSerializer
        if self.action in ('update', 'partial_update', 'corregir'):
            return ComprobanteEdicionSerializer
        return ComprobanteSerializer

    def update(self, request, *args, **kwargs):
        """Solo permite modificar directamente comprobantes BORRADOR."""
        input_ser = self.get_serializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        from apps.comprobantes.services import ComprobanteService as WebService
        modelo = WebService.actualizar_borrador(
            int(kwargs['pk']),
            dict(input_ser.validated_data),
            usuario=request.user if request.user.is_authenticated else None,
        )
        return Response(ComprobanteSerializer(modelo).data)

    def partial_update(self, request, *args, **kwargs):
        # La edicion tributaria debe ser completa para no perder lineas.
        return self.update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Delega al servicio de dominio."""
        input_ser = self.get_serializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data
        service = get_comprobante_service()
        creado_por_id = (
            request.user.id if request.user.is_authenticated else None
        )
        try:
            comprobante = service.crear(
                empresa_id=data['empresa_id'],
                cliente_id=data['cliente_id'],
                fecha=data['fecha'],
                tipo=data['tipo'],
                detalles_data=list(data['detalles']),
                creado_por_id=creado_por_id,
                moneda=data.get('moneda', 'PEN'),
            )
        except DomainError:
            raise  # el handler de DRF lo traduce a HTTP
        # Para la respuesta serializamos desde el modelo Django equivalente
        from apps.comprobantes.models import Comprobante as CompModel
        modelo = CompModel.objects.select_related(
            'cliente', 'empresa', 'serie'
        ).get(pk=comprobante.id)
        return Response(
            ComprobanteSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def emitir(self, request, pk=None):
        """Borra BORRADOR -> EMITIDO."""
        service = get_comprobante_service()
        comprobante = service.emitir(comprobante_id=int(pk))
        return Response(ComprobanteSerializer(
            _cargar_modelo(comprobante.id)
        ).data)

    @action(detail=True, methods=['post'])
    def reenviar(self, request, pk=None):
        """Compatibilidad: reintenta exclusivamente un ERROR_ENVIO."""
        from apps.comprobantes.services import ComprobanteService as WebService
        modelo = WebService.reintentar_envio(int(pk))
        return Response(ComprobanteSerializer(modelo).data)

    @action(detail=True, methods=['post'])
    def corregir(self, request, pk=None):
        """Crea un documento nuevo desde un rechazo y consume otro correlativo."""
        input_ser = self.get_serializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        from apps.comprobantes.services import ComprobanteService as WebService
        modelo = WebService.corregir_rechazado(
            int(pk),
            dict(input_ser.validated_data),
            usuario=request.user if request.user.is_authenticated else None,
        )
        return Response(ComprobanteSerializer(modelo).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def eliminar_soft(self, request, pk=None):
        """Soft delete (no se puede si ACEPTADO)."""
        service = get_comprobante_service()
        usuario_id = (
            request.user.id if request.user.is_authenticated else None
        )
        service.eliminar(comprobante_id=int(pk), usuario_id=usuario_id)
        return Response({'status': 'eliminado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        """Renderiza la vista imprimible del comprobante."""
        comprobante = self.get_object()
        from django.template.loader import render_to_string
        try:
            from weasyprint import HTML
        except ImportError:
            return Response(
                {'error': 'WeasyPrint no instalado'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        html_string = render_to_string('comprobantes/pdf_template.html', {
            'comprobante': comprobante,
            'detalles': comprobante.detalles.all(),
        })
        pdf_content = HTML(string=html_string).write_pdf()
        response = HttpResponse(
            pdf_content, content_type='application/pdf'
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{comprobante.nombre_xml}.pdf"'
        )
        return response

    @action(detail=True, methods=['get'])
    def xml(self, request, pk=None):
        """Descarga el XML firmado."""
        comprobante = self.get_object()
        if not comprobante.xml_firmado:
            return Response(
                {'error': 'Este comprobante no tiene XML generado'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response = HttpResponse(
            comprobante.xml_firmado.encode('utf-8'),
            content_type='application/xml',
        )
        response['Content-Disposition'] = (
            f'attachment; filename="{comprobante.nombre_xml}"'
        )
        return response

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Envia el comprobante al OSE/SUNAT."""
        service = get_sunat_service()
        try:
            resultado = service.enviar_comprobante(comprobante_id=int(pk))
        except DomainError:
            raise
        return Response(resultado)


class LogEnvioSUNATViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet read-only para el log de envios."""
    queryset = LogEnvioSUNAT.objects.select_related('comprobante').all()
    serializer_class = LogEnvioSUNATSerializer
    pagination_class = ComprobantePagination
    filterset_fields = ['comprobante', 'estado_respuesta']


def _cargar_modelo(comprobante_id):
    from apps.comprobantes.models import Comprobante as CompModel
    return CompModel.objects.select_related(
        'cliente', 'empresa', 'serie'
    ).get(pk=comprobante_id)
