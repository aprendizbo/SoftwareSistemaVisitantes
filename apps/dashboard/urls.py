from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Esto conecta la raíz con la vista del panel principal
    path('', views.dashboard, name='dashboard'),
    
    # Rutas para el detalle de las métricas del dashboard
    path(
        'detalle/en-instalaciones/',
        views.detalle_en_instalaciones,
        name='detalle_en_instalaciones'
    ),
    path(
        'detalle/visitantes-dia/',
        views.detalle_visitantes_dia,
        name='detalle_visitantes_dia'
    ),
    path(
        'detalle/entrevistas/',
        views.detalle_entrevistas,
        name='detalle_entrevistas'
    ),
    path(
        'detalle/permisos/',
        views.detalle_permisos,
        name='detalle_permisos'
    ),
]