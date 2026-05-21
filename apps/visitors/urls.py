from django.urls import path
from . import views

app_name = 'visitors'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('ingreso/', views.registrar_ingreso, name='registrar_ingreso'),

    # Checkout
    path('checkout/', views.checkout_scanner, name='checkout'),
    path('checkout/<str:token>/', views.checkout_por_token, name='checkout_token'),
    path('checkout/confirmar/<int:visit_id>/', views.confirmar_checkout, name='confirmar_checkout'),
    
    # Ruta para salida inmediata desde el botón del Dashboard
    path('salida/<int:visita_id>/', views.registrar_salida, name='registrar_salida'),
]