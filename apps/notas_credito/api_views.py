from rest_framework import viewsets, status
from rest_framework.response import Response
from apps.notas_credito.models import NotaCredito
from apps.notas_credito.serializers import NotaCreditoSerializer, NotaCreditoCreateSerializer


class NotaCreditoViewSet(viewsets.ModelViewSet):
    queryset = NotaCredito.objects.select_related('comprobante_referencia').all()
    filterset_fields = ['estado', 'tipo_nota']

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