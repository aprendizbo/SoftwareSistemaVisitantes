import base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.utils import timezone

from apps.visitors.forms import (
    VisitorForm,
    VisitForm,
    EmployeePermissionForm,
    EarlyDepartureForm,
)
from apps.employees.models import Employee, EarlyDeparture
from .email import enviar_alerta_email


@login_required
def registrar_salida_temprana(request):

    if request.method != 'POST':
        return render(
            request,
            'visitors/registrar_ingreso.html',
            {
                'visitor_form': VisitorForm(),
                'visit_form': VisitForm(),
                'permission_form': EmployeePermissionForm(),
                'early_departure_form': EarlyDepartureForm(),
            }
        )

    post_data = request.POST.copy()

    document_id = post_data.get('document_id')
    first_name = post_data.get('first_name', '')
    last_name = post_data.get('last_name', '')

    if not document_id:
        messages.error(
            request,
            'El número de documento es obligatorio para '
            'registrar la salida temprana.'
        )

        return render(
            request,
            'visitors/registrar_ingreso.html',
            {
                'visitor_form': VisitorForm(post_data),
                'visit_form': VisitForm(post_data),
                'permission_form': EmployeePermissionForm(post_data),
                'early_departure_form': EarlyDepartureForm(post_data),
            }
        )

    early_departure_form = EarlyDepartureForm(
        post_data,
        request.FILES
    )

    if not early_departure_form.is_valid():
        messages.error(
            request,
            'Verifica el responsable, detalle y correo '
            'de notificación.'
        )

        return render(
            request,
            'visitors/registrar_ingreso.html',
            {
                'visitor_form': VisitorForm(post_data),
                'visit_form': VisitForm(post_data),
                'permission_form': EmployeePermissionForm(post_data),
                'early_departure_form': early_departure_form,
            }
        )

    # =========================================================
    # BUSCAR / CREAR EMPLEADO
    # =========================================================

    empleado, creado = Employee.objects.get_or_create(
        employee_id=document_id,
        defaults={
            'first_name': first_name,
            'last_name': last_name,
            'document_type': post_data.get(
                'document_type',
                'cedula'
            ),
            'area': post_data.get(
                'area',
                ''
            ),
            'company': 'BOCCHERINI S.A.S',
            'phone_number': post_data.get(
                'phone_number',
                ''
            ),
            'emergency_contact_name': post_data.get(
                'emergency_contact_name',
                ''
            ),
            'emergency_contact_relationship': post_data.get(
                'emergency_contact_relationship',
                ''
            ),
            'emergency_contact': post_data.get(
                'emergency_contact_phone',
                ''
            ),
        }
    )

    if not creado:
        empleado.first_name = first_name
        empleado.last_name = last_name
        empleado.document_type = post_data.get(
            'document_type',
            empleado.document_type
        )
        empleado.area = post_data.get(
            'area',
            empleado.area
        )
        empleado.company = 'BOCCHERINI S.A.S'
        empleado.phone_number = post_data.get(
            'phone_number',
            ''
        )
        empleado.emergency_contact_name = post_data.get(
            'emergency_contact_name',
            ''
        )
        empleado.emergency_contact_relationship = post_data.get(
            'emergency_contact_relationship',
            ''
        )
        empleado.emergency_contact = post_data.get(
            'emergency_contact_phone',
            ''
        )
        empleado.save()

    # =========================================================
    # OBTENER FOTO
    # =========================================================

    photo_data = post_data.get('photo_base64', '')
    imagen_bytes = None

    print("=== FOTO SALIDA TEMPRANA ===")
    print("photo_data recibido:", bool(photo_data))
    print("longitud photo_data:", len(photo_data))

    if photo_data and 'base64,' in photo_data:
        try:
            _, imgstr = photo_data.split(';base64,', 1)
            imagen_bytes = base64.b64decode(imgstr)
        except Exception:
            imagen_bytes = None

    print("imagen_bytes:", bool(imagen_bytes))
    print(
        "tamaño imagen_bytes:",
        len(imagen_bytes) if imagen_bytes else 0
    )

    # Si no se tomó una foto nueva, buscar la última foto del empleado
    if not imagen_bytes:
        ultimo_permiso = (
            empleado.employeepermission_set
            .filter(photo__isnull=False)
            .exclude(photo='')
            .order_by('-id')
            .first()
        )

        if ultimo_permiso and ultimo_permiso.photo:
            try:
                with ultimo_permiso.photo.open('rb') as archivo:
                    imagen_bytes = archivo.read()
            except Exception:
                imagen_bytes = None

    # =========================================================
    # CREAR SALIDA TEMPRANA
    # =========================================================

    salida = early_departure_form.save(
        commit=False
    )

    salida.employee = empleado
    salida.document_type = empleado.document_type
    salida.document_id = empleado.employee_id
    salida.first_name = empleado.first_name
    salida.last_name = empleado.last_name
    salida.area = empleado.area or ''
    salida.company = empleado.company or 'BOCCHERINI S.A.S'
    
    salida.correo_notificar = (
        early_departure_form.cleaned_data.get(
            'correo_notificar'
        )
    )

    # =========================================================
    # DATOS AUTOMÁTICOS DE LA SALIDA
    # =========================================================
    ahora = timezone.localtime()

    # =========================================================
    # UNA SOLA SALIDA TEMPRANA POR EMPLEADO AL DÍA
    # =========================================================
    salida_existente = EarlyDeparture.objects.filter(
        document_id=empleado.employee_id,
        departure_date=ahora.date()
    ).first()

    if salida_existente:
        messages.error(
            request,
            f'El empleado con número de cédula '
            f'{empleado.employee_id} ya realizó una salida temprana '
            f'el día {ahora.date().strftime("%d/%m/%Y")}.'
        )

        return render(
            request,
            'visitors/registrar_ingreso.html',
            {
                'visitor_form': VisitorForm(post_data),
                'visit_form': VisitForm(post_data),
                'permission_form': EmployeePermissionForm(post_data),
                'early_departure_form': early_departure_form,
            }
        )

    salida.departure_date = ahora.date()
    salida.departure_time = ahora.time()

    # Usuario que registra el movimiento
    salida.usuario_registro = request.user

    # Responsable escrito manualmente en el formulario
    salida.autorizado_por = (
        early_departure_form.cleaned_data.get(
            'autorizado_por'
        )
    )
        
    salida.save()

    # =========================================================
    # GUARDAR FOTOGRAFÍA EN EL HISTÓRICO
    # =========================================================
    if imagen_bytes:
        salida.photo.save(
            f'salida_temprana_{salida.id}.jpg',
            ContentFile(imagen_bytes),
            save=True
        )

    # =========================================================
    # CORREO
    # =========================================================

    nombre_completo_emp = (
        f'{empleado.first_name} '
        f'{empleado.last_name}'
    )

    correo_destino = salida.correo_notificar

    asunto_salida = (
        f'🚨 Salida Temprana: '
        f'{nombre_completo_emp}'
    )

    contexto_salida = {
        'movimiento': 'salida_temprana',
        'es_permiso_empleado': False,
        'es_salida_temprana': True,
        'empleado': empleado,
        'salida_temprana': salida,
        'documento': empleado.employee_id,
        'nombre_completo': nombre_completo_emp,
        'empresa': empleado.company,
        'area': empleado.area,
        'celular': empleado.phone_number,
        'contacto_emergencia': (
            empleado.emergency_contact_name
        ),
        'telefono_emergencia': (
            empleado.emergency_contact
        ),
        'fecha_salida': salida.departure_date,
        'hora_salida': salida.departure_time,
        'detalle_salida': salida.detail,
        'autorizado_por': salida.autorizado_por,
        'hora_movimiento': ahora,
        'imagen_disponible': bool(salida.photo),
    }

    if correo_destino:
        enviar_alerta_email(
            asunto_salida,
            correo_destino,
            contexto_salida,
            imagen_bytes
        )

    messages.success(
        request,
        f'Salida temprana registrada correctamente '
        f'para {nombre_completo_emp}.'
    )

    return render(
        request,
        'visitors/registrar_ingreso.html',
        {
            'visitor_form': VisitorForm(),
            'visit_form': VisitForm(),
            'permission_form': EmployeePermissionForm(),
            'early_departure_form': EarlyDepartureForm(),
        }
    )