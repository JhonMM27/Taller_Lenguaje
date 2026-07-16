"""
URLs de la API hexagonal.

Centraliza los routers y endpoints REST del proyecto.
"""
from __future__ import annotations

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from interfaces.api.comprobante_views import (
    ComprobanteViewSet,
    LogEnvioSUNATViewSet,
)
from interfaces.api.nota_credito_views import NotaCreditoViewSet
from interfaces.api.cliente_views import ClienteViewSet
from interfaces.api.producto_views import ProductoViewSet
from interfaces.api.health import HealthView
from apps.reportes.views import ReporteVentasPeriodoView, DashboardView


router = DefaultRouter()
router.register(r'comprobantes', ComprobanteViewSet, basename='comprobante')
router.register(r'facturas', ComprobanteViewSet, basename='factura')
router.register(r'boletas', ComprobanteViewSet, basename='boleta')
router.register(r'notas-credito', NotaCreditoViewSet, basename='nota-credito')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'logs-sunat', LogEnvioSUNATViewSet, basename='log-sunat')


urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('health/', HealthView.as_view(), name='health'),
    path('reportes/ventas-por-periodo/', ReporteVentasPeriodoView.as_view(), name='reporte_ventas_periodo'),
    path('reportes/dashboard/', DashboardView.as_view(), name='api_dashboard'),
]