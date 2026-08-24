import base64
import io

import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.utils import timezone

from apps.visitors.forms import (
    VisitorForm,
    VisitForm,
    EmployeePermissionForm,
)
from apps.visitors.models import Visitor, Visit
from apps.employees.models import Employee, EmployeePermission
from .email import enviar_alerta_email


def obtener_imagen_base64(photo_data):
    """
    Convierte una imagen enviada en base64 a bytes.
    Retorna None si no existe o si la información es inválida.
    """
    if not photo_data or 'base64,' not in photo_data:
        return None

    try:
        _, imgstr = photo_data.split(';base64,', 1)
        return base64.b64decode(imgstr)
    except Exception:
        return None


def leer_foto_storage(photo_field):
    """
    Lee una fotografía almacenada y devuelve sus bytes.
    """
    if not photo_field:
        return None

    try:
        with photo_field.open('rb') as archivo:
            return archivo.read()
    except Exception:
        return None


def generar_qr_base64(token):
    """
    Genera el código QR del token y lo devuelve en base64.
    """
    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4
    )

    qr.add_data(token)
    qr.make(fit=True)

    buffer = io.BytesIO()

    qr.make_image(
        fill_color='black',
        back_color='white'
    ).save(
        buffer,
        format='PNG'
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode('utf-8')


@login_required
def registrar_ingreso(request):
    if request.method == 'POST':

        post_data = request.POST.copy()
        tipo_ingreso = post_data.get('visitor_type', '')

        visitor_instance = None
        document_id = post_data.get('document_id')

        if document_id:
            visitor_instance = Visitor.objects.filter(
                document_id=document_id
            ).first()

        v_form = VisitorForm(
            post_data,
            instance=visitor_instance
        )

        vi_form = VisitForm(
            post_data,
            request.FILES
        )

        permission_form = EmployeePermissionForm(
            post_data,
            request.FILES
        )

        es_permiso_empleado = (
            tipo_ingreso == 'permiso_empleado'
        )

        # =========================================================
        # FLUJO A: EN PERMISO - EMPLEADOS
        # =========================================================
        if es_permiso_empleado:

            document_id = post_data.get('document_id')
            first_name = post_data.get('first_name', '')
            last_name = post_data.get('last_name', '')

            if not document_id:
                messages.error(
                    request,
                    "El número de documento es obligatorio para procesar el permiso."
                )

                return render(
                    request,
                    'visitors/registrar_ingreso.html',
                    {
                        'visitor_form': v_form,
                        'visit_form': vi_form,
                        'permission_form': permission_form,
                    }
                )

            if not permission_form.is_valid():
                messages.error(
                    request,
                    "Verifica el tipo de permiso, el detalle y el correo de notificación."
                )

                return render(
                    request,
                    'visitors/registrar_ingreso.html',
                    {
                        'visitor_form': v_form,
                        'visit_form': vi_form,
                        'permission_form': permission_form,
                    }
                )

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
                    'cedula'
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

            tipo_permiso = permission_form.cleaned_data.get(
                'permit_type'
            )

            photo_data = request.POST.get(
                'photo_base64',
                ''
            )
            
            imagen_bytes_adjuntar = obtener_imagen_base64(
                photo_data
            )

            if not imagen_bytes_adjuntar:

                ultimo_permiso = (
                    EmployeePermission.objects
                    .filter(
                        employee=empleado,
                        photo__isnull=False
                    )
                    .exclude(photo='')
                    .order_by('-id')
                    .first()
                )

                if ultimo_permiso and ultimo_permiso.photo:
                    imagen_bytes_adjuntar = leer_foto_storage(
                        ultimo_permiso.photo
                    )

            detalle_permiso = permission_form.cleaned_data.get(
                'detalle_adicional'
            )

            correo_destino = permission_form.cleaned_data.get(
                'correo_notificar'
            )

            permiso = EmployeePermission.objects.create(
                employee=empleado,
                permit_type=tipo_permiso,
                status='ACTIVO',
                correo_notificar=correo_destino,
                detalle_adicional=detalle_permiso,
            )

            if hasattr(permiso, 'photo') and imagen_bytes_adjuntar and not permiso.photo:
                permiso.photo.save(
                    f"permiso_{permiso.id}.jpg",
                    ContentFile(
                        imagen_bytes_adjuntar
                    ),
                    save=True
                )

            nombre_completo_emp = (
                f"{empleado.first_name} "
                f"{empleado.last_name}"
            )

            asunto_emp = (
                f"🚨 Empleado en Permiso: "
                f"{nombre_completo_emp}"
            )

            if permiso.correo_notificar:
                contexto_emp = {
                    'movimiento': 'salida',
                    'es_permiso_empleado': True,
                    'empleado': empleado,
                    'documento': document_id,
                    'nombre_completo': nombre_completo_emp,
                    'tipo_permiso': tipo_permiso,
                    'detalle_permiso': detalle_permiso,
                    'token_qr': permiso.token_qr,
                    'empresa': empleado.company,
                    'area': empleado.area,
                    'celular': empleado.phone_number,
                    'contacto_emergencia': (
                        empleado.emergency_contact_name
                    ),
                    'telefono_emergencia': (
                        empleado.emergency_contact
                    ),
                    'hora_movimiento': timezone.localtime(),
                    'imagen_disponible': bool(
                        imagen_bytes_adjuntar
                    ),
                }

                enviar_alerta_email(
                    asunto_emp,
                    permiso.correo_notificar,
                    contexto_emp,
                    imagen_bytes_adjuntar
                )

            qr_base64 = generar_qr_base64(
                permiso.token_qr
            )

            visit_mock = {
                'id': permiso.id,
                'is_employee_mock': True,
                'visitor': {
                    'first_name': empleado.first_name,
                    'last_name': empleado.last_name,
                    'visitor_type': 'permiso_empleado',
                    'get_visitor_type_display':
                        'Permiso de Empleado',
                    'company': empleado.company
                },
                'token_qr': permiso.token_qr,
                'area': empleado.area,
                'entry_time': getattr(
                    permiso,
                    'departure_time',
                    timezone.now()
                ),
            }

            return render(
                request,
                'visitors/registrar_ingreso.html',
                {
                    'visitor_form': VisitorForm(),
                    'visit_form': VisitForm(),
                    'permission_form': EmployeePermissionForm(),
                    'qr_base64': qr_base64,
                    'v_exitosa': visit_mock,
                }
            )

        # =========================================================
        # FLUJO B: VISITANTES EXTERNOS
        # =========================================================
        elif (
            not es_permiso_empleado
            and v_form.is_valid()
            and vi_form.is_valid()
        ):

            document_id = (
                v_form.cleaned_data['document_id']
            )

            visitor_db, created = Visitor.objects.get_or_create(
                document_id=document_id,
                defaults={
                    'first_name': v_form.cleaned_data['first_name'],
                    'last_name': v_form.cleaned_data['last_name'],
                    'document_type': v_form.cleaned_data['document_type'],
                    'visitor_type': tipo_ingreso,
                    'company': v_form.cleaned_data['company'],
                    'phone_number': v_form.cleaned_data.get(
                        'phone_number',
                        ''
                    ),
                    'emergency_contact_name': v_form.cleaned_data.get(
                        'emergency_contact_name',
                        ''
                    ),
                    'emergency_contact_relationship': v_form.cleaned_data.get(
                        'emergency_contact_relationship',
                        ''
                    ),
                    'emergency_contact_phone': v_form.cleaned_data.get(
                        'emergency_contact_phone',
                        ''
                    ),
                }
            )

            if not created:
                visitor_db.first_name = v_form.cleaned_data['first_name']
                visitor_db.last_name = v_form.cleaned_data['last_name']
                visitor_db.document_type = v_form.cleaned_data['document_type']
                visitor_db.visitor_type = tipo_ingreso
                visitor_db.company = v_form.cleaned_data['company']
            
                visitor_db.phone_number = v_form.cleaned_data.get(
                    'phone_number',
                    ''
                )
            
                visitor_db.emergency_contact_name = v_form.cleaned_data.get(
                    'emergency_contact_name',
                    ''
                )
            
                visitor_db.emergency_contact_relationship = v_form.cleaned_data.get(
                    'emergency_contact_relationship',
                    ''
                )
            
                visitor_db.emergency_contact_phone = v_form.cleaned_data.get(
                    'emergency_contact_phone',
                    ''
                )
            
                visitor_db.save()

            visit = vi_form.save(
                commit=False
            )

            visit.visitor = visitor_db
            visit.status = 'ingresado'
            visit.correo_notificar = (
                vi_form.cleaned_data.get(
                    'correo_notificar'
                )
            )

            visit.save()

            # =====================================================
            # FOTO
            # =====================================================

            photo_data = request.POST.get(
                'photo_base64',
                ''
            )
            
            imagen_bytes_adjuntar = obtener_imagen_base64(
                photo_data
            )
            
            if imagen_bytes_adjuntar:
                visit.photo.save(
                    f"visita_{visit.id}.jpg",
                    ContentFile(imagen_bytes_adjuntar),
                    save=True
                )

            if not imagen_bytes_adjuntar:

                ultima_visita_con_foto = (
                    Visit.objects
                    .filter(
                        visitor=visitor_db,
                        photo__isnull=False
                    )
                    .exclude(photo='')
                    .order_by('-entry_time')
                    .first()
                )

                if (
                    ultima_visita_con_foto
                    and ultima_visita_con_foto.photo
                ):

                    imagen_bytes_adjuntar = leer_foto_storage(
                        ultima_visita_con_foto.photo
                    )
                    
                    if imagen_bytes_adjuntar:
                        visit.photo = ultima_visita_con_foto.photo
                        visit.save(
                            update_fields=['photo']
                        )

            # =====================================================
            # CORREO
            # =====================================================

            correo_destino = (
                visit.correo_notificar
            )

            nom_completo = (
                f"{visitor_db.first_name} "
                f"{visitor_db.last_name}"
            )

            es_entrevistado = (
                visitor_db.visitor_type
                == 'entrevistado'
            )

            asunto_vis = (
                f"{'👤 Entrevistado' if es_entrevistado else '🔔 Visitante'} "
                f"en Instalaciones: {nom_completo}"
            )

            contexto_vis = {
                'movimiento': 'entrada',
                'es_permiso_empleado': False,
                'visitante': visitor_db,
                'visita': visit,
                'nombre_completo': nom_completo,
                'es_entrevistado': es_entrevistado,
                'empresa': visitor_db.company,
                'area': visit.area,
                'hora_movimiento': timezone.localtime(),
                'imagen_disponible': bool(
                    imagen_bytes_adjuntar
                ),
            }

            enviar_alerta_email(
                asunto_vis,
                correo_destino,
                contexto_vis,
                imagen_bytes_adjuntar
            )

            # =====================================================
            # QR
            # =====================================================

            qr_base64 = generar_qr_base64(
                visit.token_qr
            )

            return render(
                request,
                'visitors/registrar_ingreso.html',
                {
                    'visitor_form': VisitorForm(),
                    'visit_form': VisitForm(),
                    'permission_form': EmployeePermissionForm(),
                    'qr_base64': qr_base64,
                    'v_exitosa': visit,
                }
            )

        messages.error(
            request,
            "Error al registrar. Por favor verifica que todos los campos requeridos estén llenos."
        )

        return render(
            request,
            'visitors/registrar_ingreso.html',
            {
                'visitor_form': v_form,
                'visit_form': vi_form,
                'permission_form': permission_form,
            }
        )

    # =========================================================
    # FLUJO C: GET
    # =========================================================

    return render(
        request,
        'visitors/registrar_ingreso.html',
        {
            'visitor_form': VisitorForm(),
            'visit_form': VisitForm(),
            'permission_form': EmployeePermissionForm(),
        }
    )