from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Esto conecta la raíz con la vista del panel principal
    path('', views.dashboard, name='dashboard'),
]