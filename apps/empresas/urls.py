from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.lista_empresas, name='lista'),
    path('nueva/', views.crear_empresa, name='crear'),
    path('editar/<int:pk>/', views.editar_empresa, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_empresa, name='eliminar'),
]