from django.urls import path
from . import views

app_name = 'visitors'

urlpatterns = [
    # Registro de ingresos (CORREGIDO: name ahora es registrar_ingreso)
    path('ingreso/', views.registrar_ingreso, name='registrar_ingreso'),

    # Checkout / Salidas con Scanner o Token
    path('checkout/', views.checkout_scanner, name='checkout_scanner'),
    path('checkout/<str:token>/', views.checkout_por_token, name='checkout_por_token'),
    path('checkout/confirmar/<int:visit_id>/', views.confirmar_checkout, name='confirmar_checkout'),

    # Salida manual de visitantes desde el Dashboard
    path('salida/<int:visita_id>/', views.registrar_salida, name='registrar_salida'),

    # Re-ingreso manual de Empleados desde el Dashboard (CORREGIDO: name ahora es regreso_empleado)
    path('regreso-empleado/<int:permiso_id>/', views.registrar_regreso_empleado, name='regreso_empleado'),
]