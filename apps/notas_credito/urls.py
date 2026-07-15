from django.urls import path
from . import views

app_name = 'notas_credito'

urlpatterns = [
    path('', views.lista_notas_credito, name='lista'),
    path('nueva/', views.crear_nota_credito, name='crear'),
    path('<int:pk>/', views.detalle_nota_credito, name='detalle'),
    path('<int:pk>/xml/', views.descargar_xml, name='xml'),
    path('<int:pk>/cdr/', views.descargar_cdr, name='cdr'),
    path('eliminar/<int:pk>/', views.eliminar_nota_credito, name='eliminar'),
]