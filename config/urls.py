from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
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
from apps.comprobantes.api_views import ComprobanteViewSet
from apps.clientes.api_views import ClienteViewSet
from apps.productos.api_views import ProductoViewSet
from apps.notas_credito.api_views import NotaCreditoViewSet
from apps.reportes.views import (
    ReporteVentasPeriodoView,
    DashboardView,
    reporte_ventas,
    dashboard as dashboard_view
)
from apps.usuarios.views import login_page, logout_page


def home(request):
    return redirect('usuarios:login')


router = DefaultRouter()
router.register(r'facturas', ComprobanteViewSet, basename='factura')
router.register(r'boletas', ComprobanteViewSet, basename='boleta')
router.register(r'comprobantes', ComprobanteViewSet, basename='comprobante')
router.register(r'clientes', ClienteViewSet, basename='cliente')
router.register(r'productos', ProductoViewSet, basename='producto')
router.register(r'notas-credito', NotaCreditoViewSet, basename='nota-credito')

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    
    path('dashboard/', login_required(dashboard_view), name='dashboard'),
    
    path('api/', include(router.urls)),
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/login/', csrf_exempt(login_page), name='api_login'),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    path('api/reportes/ventas-por-periodo/', ReporteVentasPeriodoView.as_view(), name='reporte_ventas_periodo'),
    path('api/reportes/dashboard/', DashboardView.as_view(), name='api_dashboard'),
    path('api/ose/', include('apps.sunat_ose.urls')),
    
    path('', include('apps.usuarios.urls')),
    path('empresas/', include('apps.empresas.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('productos/', include('apps.productos.urls')),
    path('notas-credito/', include('apps.notas_credito.urls')),
    path('comprobantes/', include('apps.comprobantes.urls')),
    path('reportes/', include('apps.reportes.urls')),
]