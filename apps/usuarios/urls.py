from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
]