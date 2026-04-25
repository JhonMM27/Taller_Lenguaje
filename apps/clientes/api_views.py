from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from apps.clientes.models import Cliente
from apps.clientes.serializers import ClienteSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_doc']
    search_fields = ['num_doc', 'razon_social']

    @action(detail=False, methods=['get'])
    def buscar(self, request):
        ruc = request.GET.get('ruc', '')
        dni = request.GET.get('dni', '')
        
        if ruc:
            try:
                cliente = Cliente.objects.get(num_doc=ruc, tipo_doc='6')
                serializer = self.get_serializer(cliente)
                return Response(serializer.data)
            except Cliente.DoesNotExist:
                return Response(
                    {'error': 'Cliente no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif dni:
            try:
                cliente = Cliente.objects.get(num_doc=dni, tipo_doc='1')
                serializer = self.get_serializer(cliente)
                return Response(serializer.data)
            except Cliente.DoesNotExist:
                return Response(
                    {'error': 'Cliente no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(
            {'error': 'Debe proporcionar ruc o dni'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, methods=['get'])
    def buscar_por_ruc(self, request):
        ruc = request.GET.get('ruc', '')
        try:
            cliente = Cliente.objects.get(num_doc=ruc, tipo_doc='6')
            serializer = self.get_serializer(cliente)
            return Response(serializer.data)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def buscar_por_dni(self, request):
        dni = request.GET.get('dni', '')
        try:
            cliente = Cliente.objects.get(num_doc=dni, tipo_doc='1')
            serializer = self.get_serializer(cliente)
            return Response(serializer.data)
        except Cliente.DoesNotExist:
            return Response(
                {'error': 'Cliente no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )