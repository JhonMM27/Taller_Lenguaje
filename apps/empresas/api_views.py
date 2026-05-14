from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from apps.empresas.models import Empresa, Certificado
from apps.empresas.serializers import CertificadoSerializer, CertificadoCreateSerializer
import logging

logger = logging.getLogger(__name__)


class CertificadoViewSet(viewsets.ModelViewSet):
    queryset = Certificado.objects.select_related('empresa').all()
    serializer_class = CertificadoSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        ruc = self.request.GET.get('ruc', '')
        if ruc:
            queryset = queryset.filter(empresa__ruc=ruc)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return CertificadoCreateSerializer
        return CertificadoSerializer

    @action(detail=True, methods=['post'])
    def activar(self, request, pk=None):
        cert = self.get_object()
        with transaction.atomic():
            Certificado.objects.filter(empresa=cert.empresa, is_active=True).update(is_active=False)
            cert.is_active = True
            cert.save()
        return Response({'status': 'Certificado activado', 'id': cert.id})

    @action(detail=True, methods=['post'])
    def validar(self, request, pk=None):
        from apps.empresas.services.certificado_service import validar_pfx
        cert = self.get_object()
        pfx_bytes = bytes(cert.certificado_binario)
        from apps.empresas.services.certificado_service import decrypt_password
        password = decrypt_password(cert.contrasena)
        is_valid = validar_pfx(pfx_bytes, password)
        return Response({'valid': is_valid})
