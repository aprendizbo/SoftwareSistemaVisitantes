from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from apps.employees.models import EmployeePermission
from .email import enviar_alerta_email


@login_required
def registrar_regreso_empleado(request, permiso_id):
    if request.method == 'POST':
        permiso = get_object_or_404(
            EmployeePermission,
            id=permiso_id,
            status='ACTIVO'
        )

        permiso.status = 'FINALIZADO'
        permiso.return_time = timezone.now()
        permiso.save()

        nombre_completo_emp = (
            f"{permiso.employee.first_name} "
            f"{permiso.employee.last_name}"
        )

        if permiso.correo_notificar:
            asunto_ret = (
                f"✅ Retorno de Empleado: "
                f"{nombre_completo_emp}"
            )

            imagen_bytes_adjuntar = None

            if permiso.photo:
                try:
                    with permiso.photo.open('rb') as f:
                        imagen_bytes_adjuntar = f.read()
                except Exception as e:
                    print(
                        "ERROR OBTENIENDO FOTO DE EMPLEADO:",
                        e
                    )

            contexto_ret = {
                'movimiento': 'entrada',
                'es_permiso_empleado': True,
                'empleado': permiso.employee,
                'documento': permiso.employee.employee_id,
                'nombre_completo': nombre_completo_emp,
                'tipo_permiso': permiso.permit_type,
                'detalle_permiso': getattr(
                    permiso,
                    'detalle_adicional',
                    ''
                ),
                'token_qr': permiso.token_qr,
                'area': permiso.employee.area,
                'hora_movimiento': permiso.return_time,
                'imagen_disponible': bool(
                    imagen_bytes_adjuntar
                ),
            }

            enviar_alerta_email(
                asunto_ret,
                permiso.correo_notificar,
                contexto_ret,
                imagen_bytes_adjuntar
            )

        messages.success(
            request,
            f"Re-ingreso registrado correctamente para "
            f"{nombre_completo_emp}."
        )

    return redirect('dashboard:dashboard')