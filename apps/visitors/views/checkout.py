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
                    f"Retorno de Empleado: "
                    f"{nombre_completo_emp}"
                )

                cuerpo_ret = (
                    "Se informa que el empleado ha retornado "
                    "a las instalaciones finalizando su permiso.\n\n"
                    f"Empleado: {nombre_completo_emp}\n"
                    f"Área/Departamento: {permiso.employee.area}\n"
                    f"Hora de Retorno: "
                    f"{timezone.localtime(permiso.return_time).strftime('%H:%M')}\n\n"
                    "Atentamente,\n"
                    "Sistema de Control de Accesos Boccherini."
                )

                enviar_alerta_email(
                    asunto_ret,
                    cuerpo_ret,
                    permiso.correo_notificar
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
                f"Salida de Visitante: {nom_completo}"
            )

            cuerpo_sal = (
                "Se informa que el visitante ha registrado "
                "su salida de las instalaciones.\n\n"
                f"Visitante: {nom_completo}\n"
                f"Documento: {visit.visitor.document_id}\n"
                f"Empresa / Procedencia: "
                f"{visit.visitor.company or 'Particular'}\n"
                f"Hora de Salida: "
                f"{timezone.localtime(visit.exit_time).strftime('%H:%M')}\n\n"
                "Atentamente,\n"
                "Sistema de Control de Accesos Boccherini."
            )

            enviar_alerta_email(
                asunto_sal,
                cuerpo_sal,
                visit.correo_notificar
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

        permiso = EmployeePermission.objects.filter(
            id=visita_id,
            status='ACTIVO'
        ).first()

        if permiso:
            permiso.status = 'FINALIZADO'
            permiso.return_time = timezone.now()
            permiso.save()

            nombre_completo_emp = (
                f"{permiso.employee.first_name} "
                f"{permiso.employee.last_name}"
            )

            if permiso.correo_notificar:
                asunto_ret = (
                    f"Retorno de Empleado: "
                    f"{nombre_completo_emp}"
                )

                cuerpo_ret = (
                    "Se informa que el empleado ha retornado "
                    "a las instalaciones finalizando su permiso.\n\n"
                    f"Empleado: {nombre_completo_emp}\n"
                    f"Área/Departamento: {permiso.employee.area}\n"
                    f"Hora de Retorno: "
                    f"{timezone.localtime(permiso.return_time).strftime('%H:%M')}\n\n"
                    "Atentamente,\n"
                    "Sistema de Control de Accesos Boccherini."
                )

                enviar_alerta_email(
                    asunto_ret,
                    cuerpo_ret,
                    permiso.correo_notificar
                )

            messages.success(
                request,
                f"Re-ingreso laboral registrado para "
                f"{nombre_completo_emp}."
            )

        else:
            visit = get_object_or_404(
                Visit,
                id=visita_id,
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
                    f"Salida de Visitante: {nom_completo}"
                )

                cuerpo_sal = (
                    "Se informa que el visitante ha registrado "
                    "su salida de las instalaciones.\n\n"
                    f"Visitante: {nom_completo}\n"
                    f"Documento: {visit.visitor.document_id}\n"
                    f"Empresa / Procedencia: "
                    f"{visit.visitor.company or 'Particular'}\n"
                    f"Hora de Salida: "
                    f"{timezone.localtime(visit.exit_time).strftime('%H:%M')}\n\n"
                    "Atentamente,\n"
                    "Sistema de Control de Accesos Boccherini."
                )

                enviar_alerta_email(
                    asunto_sal,
                    cuerpo_sal,
                    visit.correo_notificar
                )

            messages.success(
                request,
                f"Salida registrada exitosamente para "
                f"{visit.visitor.first_name} "
                f"{visit.visitor.last_name}."
            )

    return redirect('dashboard:dashboard')