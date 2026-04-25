from django.urls import path
from . import views

app_name = 'productos'

urlpatterns = [
    path('', views.lista_productos, name='lista'),
    path('nuevo/', views.crear_producto, name='crear'),
    path('editar/<int:pk>/', views.editar_producto, name='editar'),
    path('eliminar/<int:pk>/', views.eliminar_producto, name='eliminar'),
    path('categorias/', views.lista_categorias, name='categorias_lista'),
    path('categorias/nuevo/', views.crear_categoria, name='categorias_crear'),
    path('categorias/editar/<int:pk>/', views.editar_categoria, name='categorias_editar'),
    path('categorias/eliminar/<int:pk>/', views.eliminar_categoria, name='categorias_eliminar'),
]