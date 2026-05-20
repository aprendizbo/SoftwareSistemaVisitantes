from django.urls import path
from . import views

app_name = 'visitors'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ingreso/', views.registrar_ingreso, name='registrar_ingreso'),
]