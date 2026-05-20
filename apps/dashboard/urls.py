from django.urls import path
from . import views

urlpatterns = [
    # Esto conecta la raíz de la app dashboard con la función de tu views.py
    path('', views.dashboard, name='dashboard'),
]