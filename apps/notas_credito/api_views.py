from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from apps.notas_credito.models import NotaCredito, DetalleNotaCredito
from apps.notas_credito.serializers import NotaCreditoSerializer, NotaCreditoCreateSerializer, DetalleNotaCreditoSerializer
from apps.comprobantes.models import Comprobante, DetalleComprobante
from apps.comprobantes.serializers import DetalleComprobanteSerializer


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.select_related('comprobante_referencia').all()
    filterset_fields = ['estado', 'tipo_nota', 'tipo_nc']

    def get_serializer_class(self):
        if self.action == 'create':
            return NotaCreditoCreateSerializer
        return NotaCreditoSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nota = serializer.save()
        return Response(
            NotaCreditoSerializer(nota).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'])
    def buscar_comprobante(self, request):
        query = request.query_params.get('q', '')
        fecha_desde = request.query_params.get('fecha_desde', '')
        fecha_hasta = request.query_params.get('fecha_hasta', '')

        comprobantes = Comprobante.objects.filter(
            estado='ACEPTADO'
        ).select_related('cliente', 'serie')

        if query and query != '*':
            if query.isdigit():
                comprobantes = comprobantes.filter(numero=int(query))
            else:
                comprobantes = comprobantes.filter(
                    cliente__razon_social__icontains=query
                ) | comprobantes.filter(
                    cliente__codigo__icontains=query
                ) | comprobantes.filter(
                    serie__serie__icontains=query
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
        comprobante_id = request.query_params.get('comprobante_id')
        if not comprobante_id:
            return Response({'error': 'comprobante_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            comp = Comprobante.objects.get(id=comprobante_id)
        except Comprobante.DoesNotExist:
            return Response({'error': 'Comprobante no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        detalles = DetalleComprobante.objects.filter(comprobante=comp).select_related('producto')

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
            'detalles': results
        })

    @action(detail=False, methods=['get'])
    def siguiente_numero(self, request):
        serie = request.query_params.get('serie', 'FC01')
        count = NotaCredito.objects.filter(serie=serie).count()
        return Response({'serie': serie, 'numero': count + 1})
