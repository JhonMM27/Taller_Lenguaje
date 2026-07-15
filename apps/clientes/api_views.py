from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from apps.clientes.models import Cliente
from apps.clientes.serializers import ClienteSerializer
from apps.clientes.services import ClienteService


class ClienteViewSet(viewsets.ModelViewSet):
    serializer_class = ClienteSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['tipo_doc']
    search_fields = ['num_doc', 'razon_social']

    def get_queryset(self):
        return Cliente.activos.all()

    def create(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            cliente = ClienteService.crear(serializer.validated_data, usuario=request.user)
            return Response(ClienteSerializer(cliente).data, status=status.HTTP_201_CREATED)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        try:
            cliente = ClienteService.actualizar(instance.id, serializer.validated_data)
            return Response(ClienteSerializer(cliente).data)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        from apps.core.exceptions import AppError
        instance = self.get_object()
        try:
            ClienteService.eliminar(instance.id, usuario=request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AppError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

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