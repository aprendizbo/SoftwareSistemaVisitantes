from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from ..models import Visit
from apps.employees.models import EmployeePermission
from .email import enviar_alerta_email


def checkout_scanner(request):
    return render(request, 'visitors/checkout.html')


@login_required
def checkout_por_token(request, token):
    token_upper = token.upper()

    try:
        visit = Visit.objects.select_related('visitor').get(
            token_qr=token_upper,
            status='ingresado'
        )

        return render(
            request,
            'visitors/checkout.html',
            {
                'visit': visit,
                'confirmar': True,
                'es_empleado': False
            }
        )

    except Visit.DoesNotExist:
        pass

    try:
        permiso = EmployeePermission.objects.select_related(
            'employee'
        ).get(
            token_qr=token_upper,
            status='ACTIVO'
        )

        visit_mock = {
            'id': permiso.id,
            'token_qr': permiso.token_qr,
            'entry_time': getattr(
                permiso,
                'departure_time',
                timezone.now()
            ),
            'area': permiso.employee.area,
            'visitor': {
                'first_name': permiso.employee.first_name,
                'last_name': permiso.employee.last_name,
                'visitor_type': 'permiso_empleado',
                'company': 'PERSONAL INTERNO'
            }
        }

        return render(
            request,
            'visitors/checkout.html',
            {
                'visit': visit_mock,
                'confirmar': True,
                'es_empleado': True
            }
        )

    except EmployeePermission.DoesNotExist:
        return render(
            request,
            'visitors/checkout.html',
            {
                'error': f'Token "{token_upper}" no encontrado.',
                'confirmar': False
            }
        )


@require_POST
@login_required
def confirmar_checkout(request, visit_id):
    es_empleado = (
        request.POST.get('es_empleado') == 'True'
        or request.GET.get('es_empleado') == 'True'
    )

    if es_empleado:
        try:
            permiso = EmployeePermission.objects.select_related(
                'employee'
            ).get(
                id=visit_id,
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
                        print("ERROR OBTENIENDO FOTO DE EMPLEADO:", e)

                contexto = {
                    'movimiento': 'entrada', # El retorno es un ingreso a la instalación
                    'es_permiso_empleado': True,
                    'empleado': permiso.employee,
                    'documento': permiso.employee.employee_id,
                    'nombre_completo': nombre_completo_emp,
                    'tipo_permiso': permiso.permit_type,
                    'detalle_permiso': getattr(permiso, 'detalle_adicional', ''),
                    'token_qr': permiso.token_qr,
                    'area': permiso.employee.area,
                    'hora_movimiento': permiso.return_time,
                    'imagen_disponible': bool(imagen_bytes_adjuntar),
                }

                enviar_alerta_email(
                    asunto_ret,
                    permiso.correo_notificar,
                    contexto,
                    imagen_bytes_adjuntar
                )

            return JsonResponse({
                'ok': True,
                'nombre': nombre_completo_emp,
                'token': permiso.token_qr,
                'exit_time': permiso.return_time.strftime('%H:%M')
            })

        except EmployeePermission.DoesNotExist:
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'No encontrado.'
                },
                status=404
            )

    try:
        visit = Visit.objects.select_related(
            'visitor'
        ).get(
            id=visit_id,
            status='ingresado'
        )

        visit.status = 'salido'
        visit.exit_time = timezone.now()
        visit.save()

        if visit.correo_notificar:
            nom_completo = (
                f"{visit.visitor.first_name} "
                f"{visit.visitor.last_name}"
            )

            asunto_sal = (
                f"🚪 Salida de Visitante: {nom_completo}"
            )

            imagen_bytes_adjuntar = None

            if visit.photo:
                try:
                    with visit.photo.open('rb') as f:
                        imagen_bytes_adjuntar = f.read()

                except Exception as e:
                    print(
                        "ERROR OBTENIENDO FOTO DEL VISITANTE:",
                        e
                    )

            contexto_sal = {
                'movimiento': 'salida',
                'es_permiso_empleado': False,
                'visitante': visit.visitor,
                'visita': visit,
                'nombre_completo': nom_completo,
                'es_entrevistado': (
                    visit.visitor.visitor_type == 'entrevistado'
                ),
                'empresa': visit.visitor.company,
                'area': visit.area,
                'hora_movimiento': visit.exit_time,
                'imagen_disponible': bool(imagen_bytes_adjuntar),
            }

            enviar_alerta_email(
                asunto_sal,
                visit.correo_notificar,
                contexto_sal,
                imagen_bytes_adjuntar
            )

        return JsonResponse({
            'ok': True,
            'nombre': visit.visitor.first_name,
            'token': visit.token_qr,
            'exit_time': visit.exit_time.strftime('%H:%M')
        })

    except Visit.DoesNotExist:
        return JsonResponse(
            {
                'ok': False,
                'error': 'No encontrado.'
            },
            status=404
        )


@login_required
def registrar_salida(request, visita_id):
    if request.method == 'POST':

        # Buscamos primero el permiso SIN filtrar el estado ACTIVO
        permiso = EmployeePermission.objects.filter(
            id=visita_id
        ).first()

        if permiso:
            # Si lo encontró y ya está FINALIZADO, evitamos procesarlo otra vez
            if permiso.status == 'FINALIZADO':
                messages.info(
                    request,
                    f"El retorno laboral de {permiso.employee.first_name} {permiso.employee.last_name} ya había sido registrado anteriormente."
                )
            else:
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
                            print("ERROR OBTENIENDO FOTO DE EMPLEADO:", e)

                    contexto = {
                        'movimiento': 'entrada', # El retorno es un ingreso a la instalación
                        'es_permiso_empleado': True,
                        'empleado': permiso.employee,
                        'documento': permiso.employee.employee_id,
                        'nombre_completo': nombre_completo_emp,
                        'tipo_permiso': permiso.permit_type,
                        'detalle_permiso': getattr(permiso, 'detalle_adicional', ''),
                        'token_qr': permiso.token_qr,
                        'area': permiso.employee.area,
                        'hora_movimiento': permiso.return_time,
                        'imagen_disponible': bool(imagen_bytes_adjuntar),
                    }

                    enviar_alerta_email(
                        asunto_ret,
                        permiso.correo_notificar,
                        contexto,
                        imagen_bytes_adjuntar
                    )

                messages.success(
                    request,
                    f"Re-ingreso laboral registrado para "
                    f"{nombre_completo_emp}."
                )

        else:
            # Buscamos la visita SIN filtrar por status='ingresado'
            visit = get_object_or_404(
                Visit,
                id=visita_id
            )

            # Verificamos internamente el estado
            if visit.status == 'salido':
                messages.info(
                    request,
                    f"La salida de {visit.visitor.first_name} {visit.visitor.last_name} ya había sido registrada anteriormente."
                )
            else:
                visit.status = 'salido'
                visit.exit_time = timezone.now()
                visit.save()

                if visit.correo_notificar:
                    nom_completo = (
                        f"{visit.visitor.first_name} "
                        f"{visit.visitor.last_name}"
                    )

                    asunto_sal = (
                        f"🚪 Salida de Visitante: {nom_completo}"
                    )

                    imagen_bytes_adjuntar = None

                    if visit.photo:
                        try:
                            with visit.photo.open('rb') as f:
                                imagen_bytes_adjuntar = f.read()

                        except Exception as e:
                            print(
                                "ERROR OBTENIENDO FOTO DEL VISITANTE:",
                                e
                            )

                    contexto_sal = {
                        'movimiento': 'salida',
                        'es_permiso_empleado': False,
                        'visitante': visit.visitor,
                        'visita': visit,
                        'nombre_completo': nom_completo,
                        'es_entrevistado': (
                            visit.visitor.visitor_type == 'entrevistado'
                        ),
                        'empresa': visit.visitor.company,
                        'area': visit.area,
                        'hora_movimiento': visit.exit_time,
                        'imagen_disponible': bool(imagen_bytes_adjuntar),
                    }

                    enviar_alerta_email(
                        asunto_sal,
                        visit.correo_notificar,
                        contexto_sal,
                        imagen_bytes_adjuntar
                    )

                messages.success(
                    request,
                    f"Salida registrada exitosamente para "
                    f"{visit.visitor.first_name} "
                    f"{visit.visitor.last_name}."
                )

    return redirect('dashboard:dashboard')