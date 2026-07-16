"""
URLs principales del proyecto.

Las URLs estan divididas asi:
    /api/*        -> REST API (capa interfaces)
    /admin/       -> Django admin
    /dashboard/    -> Vista web del dashboard
    /comprobantes/ -> Vistas web templates
    /clientes/    -> Vistas web templates
    /productos/   -> Vistas web templates
    /notas-credito/ -> Vistas web templates
    /reportes/    -> Vistas web templates
    /sunat/       -> Vistas web templates (envio masivo)
"""
from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from apps.usuarios.views import login_page, logout_page
from apps.reportes.views import dashboard as dashboard_view


def home(request):
    return redirect('usuarios:login')


urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),

    # Dashboard
    path('dashboard/', login_required(dashboard_view), name='dashboard'),

    # API REST (capa hexagonal: interfaces/api)
    path('api/', include('interfaces.api.urls')),

    # Mantener compatibilidad con endpoint de login legacy
    path('api/auth/login/', csrf_exempt(login_page), name='api_login'),

    # Apps web (templates) - se mantienen las urls originales
    path('', include('apps.usuarios.urls')),
    path('empresas/', include('apps.empresas.urls')),
    path('clientes/', include('apps.clientes.urls')),
    path('productos/', include('apps.productos.urls')),
    path('notas-credito/', include('apps.notas_credito.urls')),
    path('comprobantes/', include('apps.comprobantes.urls')),
    path('reportes/', include('apps.reportes.urls')),
    path('sunat-ose/', include('apps.sunat_ose.urls')),
]