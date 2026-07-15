"""
Healthcheck endpoint.

Verifica que la aplicacion este operativa: BD + flag de modo SUNAT.
"""
from __future__ import annotations

from django.db import connection
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
import os


@method_decorator(csrf_exempt, name='dispatch')
class HealthView(APIView):
    """Endpoint de health check. Usado por load balancers y monitoring."""

    authentication_classes = []
    permission_classes = []

    def get(self, request):
        db_ok = True
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception:
            db_ok = False

        sunat_mock = os.getenv("SUNAT_OSE_MOCK", "True") == "True"

        return Response({
            "status": "ok" if db_ok else "degraded",
            "database": "ok" if db_ok else "error",
            "sunat_mock": sunat_mock,
            "debug": settings.DEBUG,
        })