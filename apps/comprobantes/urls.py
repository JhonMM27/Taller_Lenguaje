from django.urls import path
from . import views

app_name = 'comprobantes'

urlpatterns = [
    path('', views.lista_comprobantes, name='lista'),
    path('nuevo/', views.crear_comprobante, name='crear'),
    path('importar/', views.importar_csv, name='importar'),
    path('importar/plantilla/', views.descargar_plantilla_importacion, name='plantilla_importacion'),
    path('<int:pk>/', views.detalle_comprobante, name='detalle'),
    path('<int:pk>/pdf/', views.ver_pdf, name='pdf'),
    path('<int:pk>/xml/', views.descargar_xml, name='xml'),
    # Descarga de la Constancia de Recepción (CDR)
    path('<int:pk>/cdr/', views.descargar_cdr, name='cdr'),
    path('<int:pk>/excel/', views.descargar_excel_comprobante, name='excel'),
    path('<int:pk>/emitir/', views.emitir_comprobante, name='emitir'),
    path('<int:pk>/editar/', views.editar_comprobante, name='editar'),
    path('<int:pk>/corregir/', views.corregir_comprobante, name='corregir'),
    path('<int:pk>/reintentar/', views.reintentar_comprobante, name='reintentar'),
    path('buscar-empresas/', views.buscar_empresas_ajax, name='buscar_empresas'),
    path('buscar-clientes/', views.buscar_clientes_ajax, name='buscar_clientes'),
    path('buscar-productos/', views.buscar_productos_ajax, name='buscar_productos'),
]
