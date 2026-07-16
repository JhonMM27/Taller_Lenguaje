"""
ViewSets de DRF para notas de credito.

Incluye acciones personalizadas:
    - buscar_comprobante: busca comprobantes ACEPTADOS para asociar a NC
    - detalles_comprobante: obtiene los detalles de un comprobante
    - siguiente_numero: obtiene el siguiente correlativo de NC
"""
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from interfaces.container import (
    get_nota_credito_service,
    get_sunat_service,
)
from interfaces.api.serializers import (
    NotaCreditoCreateSerializer,
    NotaCreditoSerializer,
)

from apps.comprobantes.models import Comprobante, DetalleComprobante


class NotaCreditoViewSet(viewsets.ModelViewSet):
    """ViewSet delgado: solo delega al servicio de dominio."""

    queryset = Comprobante.objects.none()  # placeholder, se sobreescribe
    serializer_class = NotaCreditoSerializer
    filterset_fields = ['estado', 'tipo_nota', 'tipo_nc']

    def get_queryset(self):
        from apps.notas_credito.models import NotaCredito
        queryset = NotaCredito.activos.select_related(
            'comprobante_referencia', 'comprobante_referencia__cliente'
        ).all()
        user = self.request.user
        if user and user.is_authenticated:
            try:
                perfil = user.perfil
                if perfil.rol != 'ADMIN' and perfil.empresa:
                    queryset = queryset.filter(
                        comprobante_referencia__empresa=perfil.empresa
                    )
            except AttributeError:
                pass
        return queryset.order_by('-fecha', '-creado_en')

    def get_serializer_class(self):
        if self.action == 'create':
            return NotaCreditoCreateSerializer
        return NotaCreditoSerializer

    def create(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError, ReglaNegocioViolada, RecursoNoEncontrado
        input_ser = self.get_serializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        data = input_ser.validated_data
        service = get_nota_credito_service()
        creado_por_id = (
            request.user.id if request.user.is_authenticated else None
        )
        try:
            nota = service.emitir(
                comprobante_referencia_id=data['comprobante_id'],
                tipo_nc=data['tipo_nc'],
                tipo_nota=data['tipo_nota'],
                descripcion=data.get('descripcion', ''),
                detalles_data=list(data.get('detalles', []) or []),
                creado_por_id=creado_por_id,
            )
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ReglaNegocioViolada as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        modelo = self.get_queryset().get(pk=nota.id)
        return Response(
            NotaCreditoSerializer(modelo).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'])
    def enviar(self, request, pk=None):
        """Envia la NC al OSE/SUNAT."""
        from apps.core.exceptions import DomainError
        service = get_sunat_service()
        try:
            resultado = service.enviar_nota_credito(nota_id=int(pk))
        except DomainError:
            raise
        return Response(resultado)

    def destroy(self, request, *args, **kwargs):
        from apps.core.exceptions import RecursoNoEncontrado
        nota = self.get_object()
        service = get_nota_credito_service()
        usuario_id = (
            request.user.id if request.user.is_authenticated else None
        )
        try:
            service.eliminar(nota_id=nota.pk, usuario_id=usuario_id)
        except RecursoNoEncontrado as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def buscar_comprobante(self, request):
        """
        Busca comprobantes ACEPTADOS para asociar a una NC.

        Query params:
            q: texto de busqueda (codigo, serie, razon social del cliente)
            fecha_desde: fecha inicio (YYYY-MM-DD)
            fecha_hasta: fecha fin (YYYY-MM-DD)
        """
        query = request.query_params.get('q', '')
        fecha_desde = request.query_params.get('fecha_desde', '')
        fecha_hasta = request.query_params.get('fecha_hasta', '')

        comprobantes = Comprobante.objects.filter(
            estado='ACEPTADO'
        ).select_related('cliente', 'serie')

        if query and query != '*':
            from django.db.models import Q
            if query.isdigit():
                comprobantes = comprobantes.filter(numero=int(query))
            else:
                comprobantes = comprobantes.filter(
                    Q(cliente__razon_social__icontains=query)
                    | Q(cliente__codigo__icontains=query)
                    | Q(serie__serie__icontains=query)
                )

        if fecha_desde:
            comprobantes = comprobantes.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            comprobantes = comprobantes.filter(fecha__lte=fecha_hasta)

        comprobantes = comprobantes.order_by('-fecha', '-numero')[:50]

        results = []
        for comp in comprobantes:
            results.append({
                'id': comp.id,
                'serie': comp.serie.serie if comp.serie else '',
                'numero': f"{comp.numero:08d}",
                'numero_completo': f"{comp.serie.serie if comp.serie else ''}-{comp.numero:08d}",
                'tipo': comp.get_tipo_display(),
                'tipo_codigo': comp.tipo,
                'cliente_codigo': comp.cliente.codigo,
                'cliente_nombre': comp.cliente.razon_social,
                'cliente_documento': comp.cliente.num_doc,
                'fecha': comp.fecha.isoformat(),
                'subtotal': str(comp.subtotal),
                'igv': str(comp.igv),
                'total': str(comp.total),
                'estado': comp.estado,
            })

        return Response({'results': results})

    @action(detail=False, methods=['get'])
    def detalles_comprobante(self, request):
        """Obtiene los detalles de un comprobante para cargar en la NC."""
        comprobante_id = request.query_params.get('comprobante_id')
        if not comprobante_id:
            return Response(
                {'error': 'comprobante_id requerido'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            comp = Comprobante.objects.select_related('cliente', 'serie').get(
                id=comprobante_id
            )
        except Comprobante.DoesNotExist:
            return Response(
                {'error': 'Comprobante no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        detalles = DetalleComprobante.objects.filter(
            comprobante=comp
        ).select_related('producto')

        results = []
        for det in detalles:
            results.append({
                'id': det.id,
                'producto_id': det.producto.id,
                'producto_codigo': det.producto.codigo,
                'producto_descripcion': det.producto.descripcion,
                'cantidad': str(det.cantidad),
                'precio_unitario': str(det.precio_unitario),
                'descuento': str(det.descuento),
                'afecto_igv': det.afecto_igv,
                'cod_tipo_afectacion': det.cod_tipo_afectacion,
                'igv_linea': str(det.igv_linea),
                'subtotal': str(det.subtotal),
            })

        return Response({
            'comprobante': {
                'id': comp.id,
                'serie': comp.serie.serie if comp.serie else '',
                'numero': f"{comp.numero:08d}",
                'tipo': comp.get_tipo_display(),
                'cliente_codigo': comp.cliente.codigo,
                'cliente_nombre': comp.cliente.razon_social,
                'subtotal': str(comp.subtotal),
                'igv': str(comp.igv),
                'total': str(comp.total),
            },
            'detalles': results,
        })

    @action(detail=False, methods=['get'])
    def siguiente_numero(self, request):
        """Retorna el siguiente numero de NC para una serie."""
        from apps.notas_credito.models import NotaCredito
        serie = request.query_params.get('serie', 'FC01')
        count = NotaCredito.objects.filter(serie=serie).count()
        return Response({'serie': serie, 'numero': count + 1})