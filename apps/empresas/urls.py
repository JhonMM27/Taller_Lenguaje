from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .api_views import CertificadoViewSet

app_name = 'empresas'

router = DefaultRouter()
router.register(r'certificados', CertificadoViewSet, basename='certificado')

urlpatterns = [
    path('', views.lista_empresas, name='lista'),
    path('nueva/', views.crear_empresa, name='crear'),
    path('editar/<int:pk>/', views.editar_empresa, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_empresa, name='eliminar'),
] + router.urls