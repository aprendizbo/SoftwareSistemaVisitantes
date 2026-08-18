import base64
import io

import qrcode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.utils import timezone
from django.utils.crypto import get_random_string

from apps.visitors.forms import VisitorForm, VisitForm
from apps.visitors.models import Visitor, Visit
from apps.employees.models import Employee, EmployeePermission
from ..legacy_views import enviar_alerta_email


@login_required
def registrar_ingreso(request):
    if request.method == 'POST':

        print("====================================")
        print("TIPO:", request.POST.get('visitor_type'))
        print("PHOTO:", request.POST.get('photo_base64'))
        print("LEN:", len(request.POST.get('photo_base64', '')))
        print("====================================")

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
            area_empleado = post_data.get(
                'area',
                'RECEPCION'
            )
            empresa_empleado = post_data.get(
                'company',
                ''
            )
            motivo_form = post_data.get(
                'reason_type',
                'PERSONAL'
            )

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
                        'visit_form': vi_form
                    }
                )

            empleado, creado = Employee.objects.get_or_create(
                employee_id=document_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'company': 'BOCCHERINI S.A.S',
                    'area': area_empleado,
                    'phone_number': post_data.get('phone_number', ''),
                    'emergency_contact_name': post_data.get(
                        'emergency_contact_name',
                        ''
                    ),
                    'emergency_contact': post_data.get(
                        'emergency_contact',
                        ''
                    ),
                }
            )

            if not creado:
                empleado.first_name = first_name
                empleado.last_name = last_name
                empleado.area = area_empleado
                empleado.company = 'BOCCHERINI S.A.S'
                empleado.phone_number = post_data.get('phone_number', '')
                empleado.emergency_contact_name = post_data.get('emergency_contact_name', '')
                empleado.emergency_contact = post_data.get('emergency_contact', '')
                empleado.save()

            tipo_permiso = 'LABORAL'

            if motivo_form == 'entrevista':
                tipo_permiso = 'MEDICINA'
            elif motivo_form == 'otro':
                tipo_permiso = 'PERSONAL'

            token_nuevo = get_random_string(
                length=8
            ).upper()

            photo_data = request.POST.get(
                'photo_base64',
                ''
            )

            print(
                "PERMISO FOTO LEN:",
                len(photo_data)
            )

            print(
                "PERMISO FOTO PRESENTE:",
                bool(photo_data)
            )

            imagen_bytes_adjuntar = None

            if photo_data and 'base64,' in photo_data:
                try:
                    fmt, imgstr = photo_data.split(
                        ';base64,'
                    )

                    imagen_bytes_adjuntar = base64.b64decode(
                        imgstr
                    )

                except Exception:
                    pass

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
                    try:
                        with ultimo_permiso.photo.open(
                            'rb'
                        ) as f:
                            imagen_bytes_adjuntar = f.read()

                        print(
                            f"REUTILIZANDO FOTO EMPLEADO: "
                            f"{ultimo_permiso.photo.name}"
                        )

                    except Exception as e:
                        print(
                            "ERROR REUTILIZANDO FOTO EMPLEADO:",
                            e
                        )

            correo_destino = post_data.get(
                'correo_notificar'
            )

            permiso = EmployeePermission.objects.create(
                employee=empleado,
                permit_type=tipo_permiso,
                status='ACTIVO',
                token_qr=token_nuevo,
                correo_notificar=correo_destino,
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

            detalle_permiso = (
                f"• Detalle Adicional: "
                f"{post_data.get('reason_detail', '')}\n"
                if post_data.get('reason_detail', '')
                else ""
            )

            cuerpo_emp = (
                "Se informa la salida de un empleado "
                "bajo modalidad de permiso.\n\n"
                f"• Empleado: {nombre_completo_emp}\n"
                f"• Documento: {document_id}\n"
                f"• Área/Departamento: {empleado.area}\n"
                f"• Tipo de Permiso: {tipo_permiso}\n"
                f"{detalle_permiso}"
                f"• Token QR Asignado: {permiso.token_qr}\n"
                f"• Celular: {empleado.phone_number or 'No registrado'}\n"
                f"• Contacto de Emergencia: {empleado.emergency_contact_name or 'No registrado'} - {empleado.emergency_contact or 'No registrado'}\n"
                f"• Hora de Salida: "
                f"{timezone.localtime().strftime('%H:%M')}\n\n"
                "Se adjunta la fotografía tomada en recepción.\n\n"
                "Atentamente,\n"
                "Sistema de Control de Accesos Boccherini."
            )

            if permiso.correo_notificar:
                enviar_alerta_email(
                    asunto_emp,
                    cuerpo_emp,
                    permiso.correo_notificar,
                    imagen_bytes_adjuntar
                )

            qr = qrcode.QRCode(
                version=1,
                box_size=8,
                border=4
            )

            qr.add_data(
                permiso.token_qr
            )

            qr.make(
                fit=True
            )

            buffer = io.BytesIO()

            qr.make_image(
                fill_color="black",
                back_color="white"
            ).save(
                buffer,
                format='PNG'
            )

            qr_base64 = base64.b64encode(
                buffer.getvalue()
            ).decode('utf-8')

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
                    'emergency_contact': v_form.cleaned_data.get(
                        'emergency_contact',
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
            
                visitor_db.emergency_contact = v_form.cleaned_data.get(
                    'emergency_contact',
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

            print(
                "VISITANTE FOTO LEN:",
                len(photo_data)
            )

            print(
                "VISITANTE FOTO PRESENTE:",
                bool(photo_data)
            )

            imagen_bytes_adjuntar = None

            if photo_data and 'base64,' in photo_data:

                try:
                    fmt, imgstr = photo_data.split(
                        ';base64,'
                    )

                    imagen_bytes_adjuntar = (
                        base64.b64decode(imgstr)
                    )

                    visit.photo.save(
                        f"visita_{visit.id}.jpg",
                        ContentFile(
                            imagen_bytes_adjuntar
                        ),
                        save=True
                    )

                    print(
                        "FOTO NUEVA CAPTURADA"
                    )

                except Exception as e:
                    print(
                        "ERROR FOTO:",
                        e
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

                    try:
                        with ultima_visita_con_foto.photo.open(
                            'rb'
                        ) as f:
                            imagen_bytes_adjuntar = f.read()

                        visit.photo = (
                            ultima_visita_con_foto.photo
                        )

                        visit.save(
                            update_fields=['photo']
                        )

                        print(
                            f"REUTILIZANDO FOTO: "
                            f"{ultima_visita_con_foto.photo.name}"
                        )

                    except Exception as e:
                        print(
                            "ERROR REUTILIZANDO FOTO:",
                            e
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

            detalle_adicional = (
                f"• Detalle Adicional: "
                f"{visit.reason_detail}\n"
                if visit.reason_detail
                else ""
            )

            cuerpo_vis = (
                f"Se informa el ingreso de un "
                f"{'entrevistado' if es_entrevistado else 'visitante externo'}.\n\n"
                f"• Nombre Completo: {nom_completo}\n"
                f"• Tipo de Documento: "
                f"{visitor_db.get_document_type_display()}\n"
                f"• Número de Documento: "
                f"{visitor_db.document_id}\n"
                f"• Tipo de Visitante: "
                f"{visitor_db.get_visitor_type_display()}\n"
                f"• Empresa / Procedencia: "
                f"{visitor_db.company or 'Particular'}\n"
                f"• Persona a Visitar: "
                f"{visit.person_to_visit}\n"
                f"• Área de Destino: "
                f"{visit.area}\n"
                f"• Motivo de la Visita: "
                f"{visit.get_reason_type_display()}\n"
                f"{detalle_adicional}"
                f"• Token QR de Control: "
                f"{visit.token_qr}\n"
                f"• Celular: "
                f"{visitor_db.phone_number or 'No registrado'}\n"
                f"• Contacto de Emergencia: {visitor_db.emergency_contact_name or 'No registrado'}\n"
                f"• Parentesco: {visitor_db.emergency_contact_relationship or 'No registrado'}\n"
                f"• Número de Emergencia: {visitor_db.emergency_contact or 'No registrado'}\n"
                f"• Hora de Entrada: "
                f"{timezone.localtime().strftime('%H:%M')}\n\n"
                "Se adjunta la fotografía tomada en recepción.\n\n"
                "Atentamente,\n"
                "Sistema de Control de Accesos Boccherini."
            )

            enviar_alerta_email(
                asunto_vis,
                cuerpo_vis,
                correo_destino,
                imagen_bytes_adjuntar
            )

            # =====================================================
            # QR
            # =====================================================

            qr = qrcode.QRCode(
                version=1,
                box_size=8,
                border=4
            )

            qr.add_data(
                visit.token_qr
            )

            qr.make(
                fit=True
            )

            buffer = io.BytesIO()

            qr.make_image(
                fill_color="black",
                back_color="white"
            ).save(
                buffer,
                format='PNG'
            )

            qr_base64 = base64.b64encode(
                buffer.getvalue()
            ).decode('utf-8')

            return render(
                request,
                'visitors/registrar_ingreso.html',
                {
                    'visitor_form': VisitorForm(),
                    'visit_form': VisitForm(),
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
                'visit_form': vi_form
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
            'visit_form': VisitForm()
        }
    )