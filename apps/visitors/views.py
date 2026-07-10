import base64
import io
import json
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import EmailMessage
from django.conf import settings

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .forms import VisitorForm, VisitForm
from .models import Visit, Visitor
from apps.employees.models import Employee, EmployeePermission

# =========================================================
# FUNCIÓN AUXILIAR DE CORREO (ROBUSTA)
# =========================================================
def enviar_alerta_email(asunto, cuerpo, destinatario,
                        imagen_bytes=None,
                        nombre_imagen="foto_recepcion.jpg"):
    try:
        print(f"📧 Intentando enviar correo a: {destinatario}")

        email = EmailMessage(
            asunto,
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario]
        )

        print("IMAGEN ES NONE:", imagen_bytes is None)

        if imagen_bytes:
            print("ADJUNTANDO FOTO:", len(imagen_bytes))
            email.attach(
                'PRUEBA_FOTO.jpg',
                imagen_bytes,
                'image/jpeg'
            )
            print(email.attachments)

        print("TOTAL ADJUNTOS:", len(email.attachments))

        email.send(fail_silently=False)

        print(f"✅ CORREO ENVIADO A: {destinatario}")

    except Exception as e:
        print(f"❌ ERROR SMTP: {e}")


# =========================================================
# VISTAS PRINCIPALES
# =========================================================

@login_required
def registrar_ingreso(request):
    if request.method == 'POST':
        
        # --- CÓDIGO TEMPORAL PARA DEBUG ---
        print("====================================")
        print("TIPO:", request.POST.get('visitor_type'))
        print("PHOTO:", request.POST.get('photo_base64'))
        print("LEN:", len(request.POST.get('photo_base64', '')))
        print("====================================")
        # ----------------------------------

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
        vi_form = VisitForm(post_data, request.FILES)

        es_permiso_empleado = (tipo_ingreso == 'permiso_empleado')

        # =========================================================
        # FLUJO A: EN PERMISO (ÚNICAMENTE EMPLEADOS)
        # =========================================================
        if es_permiso_empleado:
            document_id = post_data.get('document_id')
            first_name = post_data.get('first_name', '')
            last_name = post_data.get('last_name', '')
            area_empleado = post_data.get('area', 'RECEPCION')
            empresa_empleado = post_data.get('company', '')
            motivo_form = post_data.get('reason_type', 'PERSONAL')

            if not document_id:
                messages.error(request, "El número de documento es obligatorio para procesar el permiso.")
                return render(request, 'visitors/registrar_ingreso.html', {'visitor_form': v_form, 'visit_form': vi_form})

            # --- CORRECCIÓN APLICADA AQUÍ: Guardar first_name y last_name ---
            empleado, creado = Employee.objects.get_or_create(
                employee_id=document_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'document_type': post_data.get('document_type', 'cedula'),
                    'area': area_empleado,
                    'company': empresa_empleado,
                }
            )

            if not creado:
                empleado.first_name = first_name
                empleado.last_name = last_name
                empleado.area = area_empleado
                empleado.company = empresa_empleado
                empleado.document_type = post_data.get('document_type', 'cedula')
                empleado.save()
            # --------------------------------------------------------

            tipo_permiso = 'LABORAL'
            if motivo_form == 'entrevista': tipo_permiso = 'MEDICINA'
            elif motivo_form == 'otro': tipo_permiso = 'PERSONAL'

            token_nuevo = get_random_string(length=8).upper()
            
            # --- CAPTURA Y DECODIFICACIÓN DE FOTO (BLOQUE PERMISO) ---
            photo_data = request.POST.get('photo_base64', '')
            print("PERMISO FOTO LEN:", len(photo_data))
            print("PERMISO FOTO PRESENTE:", bool(photo_data))
            imagen_bytes_adjuntar = None

            if photo_data and 'base64,' in photo_data:
                try:
                    fmt, imgstr = photo_data.split(';base64,')
                    imagen_bytes_adjuntar = base64.b64decode(imgstr)
                except Exception:
                    pass

            # --- NUEVO CÓDIGO AÑADIDO: Reutilizar foto de empleado ---
            if not imagen_bytes_adjuntar:
                ultimo_permiso = (
                    EmployeePermission.objects
                    .filter(
                        employee=empleado,
                        photo__isnull=False
                    )
                    .exclude(photo='')
                    .order_by('-departure_time')
                    .first()
                )

                if ultimo_permiso and ultimo_permiso.photo:
                    try:
                        with ultimo_permiso.photo.open('rb') as f:
                            imagen_bytes_adjuntar = f.read()

                        print(
                            f"♻ REUTILIZANDO FOTO EMPLEADO: "
                            f"{ultimo_permiso.photo.name}"
                        )

                    except Exception as e:
                        print(
                            "ERROR REUTILIZANDO FOTO EMPLEADO:",
                            e
                        )

            correo_destino = post_data.get('correo_notificar')
            
            # --- CREACIÓN DEL PERMISO ---
            permiso = EmployeePermission.objects.create(
                employee=empleado,
                permit_type=tipo_permiso,
                status='ACTIVO',
                token_qr=token_nuevo,
                correo_notificar=correo_destino,
                detalle_adicional=post_data.get('reason_detail', '')
            )

            # --- CAMBIO APLICADO: Verificación combinada de foto ---
            if imagen_bytes_adjuntar and not permiso.photo:
                permiso.photo.save(
                    f"permiso_{permiso.id}.jpg",
                    ContentFile(imagen_bytes_adjuntar),
                    save=True
                )

            # Referencias a nombre actualizadas
            nombre_completo_emp = f"{empleado.first_name} {empleado.last_name}"
            asunto_emp = f"🚨 Empleado en Permiso: {nombre_completo_emp}"
            detalle_permiso = f"• Detalle Adicional: {permiso.detalle_adicional}\n" if permiso.detalle_adicional else ""

            cuerpo_emp = (
                f"Se informa la salida de un empleado bajo modalidad de permiso.\n\n"
                f"• Empleado: {nombre_completo_emp}\n"
                f"• Documento: {document_id}\n"
                f"• Área/Departamento: {empleado.area}\n"
                f"• Tipo de Permiso: {tipo_permiso}\n"
                f"{detalle_permiso}"
                f"• Token QR Asignado: {permiso.token_qr}\n"
                f"• Hora de Salida: {timezone.localtime().strftime('%H:%M')}\n\n"
                f"Se adjunta la fotografía tomada en recepción.\n\n"
                f"Atentamente,\nSistema de Control de Accesos Boccherini."
            )

            if permiso.correo_notificar:
                enviar_alerta_email(asunto_emp, cuerpo_emp, permiso.correo_notificar, imagen_bytes_adjuntar)

            # Generación de QR en Base64
            qr = qrcode.QRCode(version=1, box_size=8, border=4)
            qr.add_data(permiso.token_qr)
            qr.make(fit=True)
            buffer = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            visit_mock = {
                'id': permiso.id,
                'is_employee_mock': True,
                'visitor': {
                    'first_name': empleado.first_name, 
                    'last_name': empleado.last_name, 
                    'visitor_type': 'permiso_empleado',
                    'get_visitor_type_display': 'Permiso de Empleado',
                    'company': 'PERSONAL INTERNO'
                },
                'token_qr': permiso.token_qr,
                'area': empleado.area,
                'entry_time': getattr(permiso, 'departure_time', timezone.now()),
            }

            return render(request, 'visitors/registrar_ingreso.html', {
                'visitor_form': VisitorForm(),
                'visit_form': VisitForm(),
                'qr_base64': qr_base64,
                'v_exitosa': visit_mock,
            })

        # =========================================================
        # FLUJO B: VISITANTES EXTERNOS
        # =========================================================
        elif not es_permiso_empleado and v_form.is_valid() and vi_form.is_valid():
            document_id = v_form.cleaned_data['document_id']
            
            visitor_db, created = Visitor.objects.get_or_create(
                document_id=document_id,
                defaults={
                    'first_name': v_form.cleaned_data['first_name'],
                    'last_name': v_form.cleaned_data['last_name'],
                    'document_type': v_form.cleaned_data['document_type'],
                    'visitor_type': tipo_ingreso,
                    'company': v_form.cleaned_data['company'],
                }
            )

            if not created:
                visitor_db.first_name = v_form.cleaned_data['first_name']
                visitor_db.last_name = v_form.cleaned_data['last_name']
                visitor_db.document_type = v_form.cleaned_data['document_type']
                visitor_db.visitor_type = tipo_ingreso
                visitor_db.company = v_form.cleaned_data['company']
                visitor_db.save()

            visit = vi_form.save(commit=False)
            visit.visitor = visitor_db
            visit.status = 'ingresado'
            visit.correo_notificar = vi_form.cleaned_data.get('correo_notificar')
            visit.save()

            # --- CAPTURA Y DECODIFICACIÓN DE FOTO (BLOQUE VISITANTE) ---
            photo_data = request.POST.get('photo_base64', '')
            print("VISITANTE FOTO LEN:", len(photo_data))
            print("VISITANTE FOTO PRESENTE:", bool(photo_data))
            imagen_bytes_adjuntar = None

            if photo_data and 'base64,' in photo_data:
                try:
                    fmt, imgstr = photo_data.split(';base64,')
                    imagen_bytes_adjuntar = base64.b64decode(imgstr)

                    visit.photo.save(
                        f"visita_{visit.id}.jpg",
                        ContentFile(imagen_bytes_adjuntar),
                        save=True
                    )
                    print("📷 FOTO NUEVA CAPTURADA")

                except Exception as e:
                    print("ERROR FOTO:", e)

            # Si NO tomó foto nueva, reutilizar la última foto
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

                if ultima_visita_con_foto and ultima_visita_con_foto.photo:
                    try:
                        with ultima_visita_con_foto.photo.open('rb') as f:
                            imagen_bytes_adjuntar = f.read()

                        visit.photo = ultima_visita_con_foto.photo
                        visit.save(update_fields=['photo'])

                        print(
                            f"♻ REUTILIZANDO FOTO: "
                            f"{ultima_visita_con_foto.photo.name}"
                        )

                    except Exception as e:
                        print("ERROR REUTILIZANDO FOTO:", e)

            correo_destino = visit.correo_notificar
            nom_completo = f"{visitor_db.first_name} {visitor_db.last_name}"
            
            es_entrevistado = (visitor_db.visitor_type == 'entrevistado')
            asunto_vis = f"{'👤 Entrevistado' if es_entrevistado else '🔔 Visitante'} en Instalaciones: {nom_completo}"
            detalle_adicional = f"• Detalle Adicional: {visit.reason_detail}\n" if visit.reason_detail else ""

            cuerpo_vis = (
                f"Se informa el ingreso de un {'entrevistado' if es_entrevistado else 'visitante externo'}.\n\n"
                f"• Nombre Completo: {nom_completo}\n"
                f"• Tipo de Documento: {visitor_db.get_document_type_display()}\n"
                f"• Número de Documento: {visitor_db.document_id}\n"
                f"• Tipo de Visitante: {visitor_db.get_visitor_type_display()}\n"
                f"• Empresa / Procedencia: {visitor_db.company or 'Particular'}\n"
                f"• Persona a Visitar: {visit.person_to_visit}\n"
                f"• Área de Destino: {visit.area}\n"
                f"• Motivo de la Visita: {visit.get_reason_type_display()}\n"
                f"{detalle_adicional}"
                f"• Token QR de Control: {visit.token_qr}\n"
                f"• Hora de Entrada: {timezone.localtime().strftime('%H:%M')}\n\n"
                f"Se adjunta la fotografía tomada en recepción.\n\n"
                f"Atentamente,\nSistema de Control de Accesos Boccherini."
            )

            enviar_alerta_email(asunto_vis, cuerpo_vis, correo_destino, imagen_bytes_adjuntar)

            # Generación de QR
            qr = qrcode.QRCode(version=1, box_size=8, border=4)
            qr.add_data(visit.token_qr)
            qr.make(fit=True)
            buffer = io.BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            return render(request, 'visitors/registrar_ingreso.html', {
                'visitor_form': VisitorForm(),
                'visit_form': VisitForm(),
                'qr_base64': qr_base64,
                'v_exitosa': visit,
            })
            
        # Si la petición es POST pero fallaron las validaciones de los formularios en el Flujo B
        messages.error(request, "Error al registrar. Por favor verifica que todos los campos requeridos estén llenos.")
        return render(request, 'visitors/registrar_ingreso.html', {
            'visitor_form': v_form,
            'visit_form': vi_form
        })

    # =========================================================
    # FLUJO C: SOLICITUD GET (Carga inicial de la página)
    # =========================================================
    return render(request, 'visitors/registrar_ingreso.html', {
        'visitor_form': VisitorForm(),
        'visit_form': VisitForm()
    })


@login_required
def checkout_scanner(request):
    return render(request, 'visitors/checkout.html')


@login_required
def checkout_por_token(request, token):
    token_upper = token.upper()
    try:
        visit = Visit.objects.select_related('visitor').get(token_qr=token_upper, status='ingresado')
        return render(request, 'visitors/checkout.html', {'visit': visit, 'confirmar': True, 'es_empleado': False})
    except Visit.DoesNotExist:
        pass

    try:
        permiso = EmployeePermission.objects.select_related('employee').get(token_qr=token_upper, status='ACTIVO')
        visit_mock = {
            'id': permiso.id,
            'token_qr': permiso.token_qr,
            'entry_time': getattr(permiso, 'departure_time', timezone.now()),
            'area': permiso.employee.area,
            'visitor': {
                'first_name': permiso.employee.first_name, 
                'last_name': permiso.employee.last_name, 
                'visitor_type': 'permiso_empleado',
                'company': 'PERSONAL INTERNO'
            }
        }
        return render(request, 'visitors/checkout.html', {'visit': visit_mock, 'confirmar': True, 'es_empleado': True})
    except EmployeePermission.DoesNotExist:
        return render(request, 'visitors/checkout.html', {'error': f'Token "{token_upper}" no encontrado.', 'confirmar': False})


@require_POST
@login_required
def confirmar_checkout(request, visit_id):
    es_empleado = request.POST.get('es_empleado') == 'True' or request.GET.get('es_empleado') == 'True'
    
    if es_empleado:
        try:
            permiso = EmployeePermission.objects.select_related('employee').get(id=visit_id, status='ACTIVO')
            permiso.status = 'FINALIZADO'
            permiso.return_time = timezone.now()
            permiso.save()

            nombre_completo_emp = f"{permiso.employee.first_name} {permiso.employee.last_name}"

            if permiso.correo_notificar:
                asunto_ret = f"✅ Retorno de Empleado: {nombre_completo_emp}"
                cuerpo_ret = (
                    f"Se informa que el empleado ha retornado a las instalaciones finalizando su permiso.\n\n"
                    f"• Empleado: {nombre_completo_emp}\n"
                    f"• Área/Departamento: {permiso.employee.area}\n"
                    f"• Hora de Retorno: {timezone.localtime(permiso.return_time).strftime('%H:%M')}\n\n"
                    f"Atentamente,\nSistema de Control de Accesos Boccherini."
                )
                enviar_alerta_email(asunto_ret, cuerpo_ret, permiso.correo_notificar)

            return JsonResponse({'ok': True, 'nombre': nombre_completo_emp, 'token': permiso.token_qr, 'exit_time': permiso.return_time.strftime('%H:%M')})
        except EmployeePermission.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No encontrado.'}, status=404)
            
    else:
        try:
            visit = Visit.objects.select_related('visitor').get(id=visit_id, status='ingresado')
            visit.status = 'salido'
            visit.exit_time = timezone.now()
            visit.save()

            if visit.correo_notificar:
                nom_completo = f"{visit.visitor.first_name} {visit.visitor.last_name}"
                asunto_sal = f"🚪 Salida de Visitante: {nom_completo}"
                cuerpo_sal = (
                    f"Se informa que el visitante ha registrado su salida de las instalaciones.\n\n"
                    f"• Visitante: {nom_completo}\n"
                    f"• Documento: {visit.visitor.document_id}\n"
                    f"• Empresa / Procedencia: {visit.visitor.company or 'Particular'}\n"
                    f"• Hora de Salida: {timezone.localtime(visit.exit_time).strftime('%H:%M')}\n\n"
                    f"Atentamente,\nSistema de Control de Accesos Boccherini."
                )
                enviar_alerta_email(asunto_sal, cuerpo_sal, visit.correo_notificar)

            return JsonResponse({'ok': True, 'nombre': f"{visit.visitor.first_name}", 'token': visit.token_qr, 'exit_time': visit.exit_time.strftime('%H:%M')})
        except Visit.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No encontrado.'}, status=404)


@login_required
def registrar_salida(request, visita_id):
    if request.method == 'POST':
        permiso = EmployeePermission.objects.filter(id=visita_id, status='ACTIVO').first()
        
        if permiso:
            permiso.status = 'FINALIZADO'
            permiso.return_time = timezone.now()
            permiso.save()

            nombre_completo_emp = f"{permiso.employee.first_name} {permiso.employee.last_name}"

            if permiso.correo_notificar:
                asunto_ret = f"✅ Retorno de Empleado: {nombre_completo_emp}"
                cuerpo_ret = (
                    f"Se informa que el empleado ha retornado a las instalaciones finalizando su permiso.\n\n"
                    f"• Empleado: {nombre_completo_emp}\n"
                    f"• Área/Departamento: {permiso.employee.area}\n"
                    f"• Hora de Retorno: {timezone.localtime(permiso.return_time).strftime('%H:%M')}\n\n"
                    f"Atentamente,\nSistema de Control de Accesos Boccherini."
                )
                enviar_alerta_email(asunto_ret, cuerpo_ret, permiso.correo_notificar)

            messages.success(request, f"Re-ingreso laboral registrado para {nombre_completo_emp}.")
            
        else:
            visit = get_object_or_404(Visit, id=visita_id, status='ingresado')
            visit.status = 'salido'
            visit.exit_time = timezone.now()
            visit.save()

            if visit.correo_notificar:
                nom_completo = f"{visit.visitor.first_name} {visit.visitor.last_name}"
                asunto_sal = f"🚪 Salida de Visitante: {nom_completo}"
                cuerpo_sal = (
                    f"Se informa que el visitante ha registrado su salida de las instalaciones.\n\n"
                    f"• Visitante: {nom_completo}\n"
                    f"• Documento: {visit.visitor.document_id}\n"
                    f"• Empresa / Procedencia: {visit.visitor.company or 'Particular'}\n"
                    f"• Hora de Salida: {timezone.localtime(visit.exit_time).strftime('%H:%M')}\n\n"
                    f"Atentamente,\nSistema de Control de Accesos Boccherini."
                )
                enviar_alerta_email(asunto_sal, cuerpo_sal, visit.correo_notificar)

            messages.success(request, f"Salida registrada exitosamente para {visit.visitor.first_name} {visit.visitor.last_name}.")
            
    return redirect('dashboard:dashboard')


@login_required
def registrar_regreso_empleado(request, permiso_id):
    if request.method == 'POST':
        permiso = get_object_or_404(EmployeePermission, id=permiso_id, status='ACTIVO')
        permiso.status = 'FINALIZADO'
        permiso.return_time = timezone.now()
        permiso.save()

        nombre_completo_emp = f"{permiso.employee.first_name} {permiso.employee.last_name}"
        
        if permiso.correo_notificar:
            asunto_ret = f"✅ Retorno de Empleado: {nombre_completo_emp}"
            cuerpo_ret = (
                f"Se informa que el empleado ha retornado a las instalaciones finalizando su permiso.\n\n"
                f"• Empleado: {nombre_completo_emp}\n"
                f"• Área/Departamento: {permiso.employee.area}\n"
                f"• Hora de Retorno: {timezone.localtime(permiso.return_time).strftime('%H:%M')}\n\n"
                f"Atentamente,\nSistema de Control de Accesos Boccherini."
            )
            enviar_alerta_email(asunto_ret, cuerpo_ret, permiso.correo_notificar)

        messages.success(request, f"Re-ingreso registrado correctamente para {nombre_completo_emp}.")
    return redirect('dashboard:dashboard')


def login_view(request):
    if request.user.is_authenticated: return redirect('dashboard:dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(username=form.cleaned_data.get('username'), password=form.cleaned_data.get('password'))
            if user is not None:
                login(request, user)
                return redirect('dashboard:dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# =========================================================
# VISTAS PARA BÚSQUEDA ASÍNCRONA (JSON)
# =========================================================

@login_required
def buscar_visitante(request):
    document_id = request.GET.get('document_id')

    if not document_id:
        return JsonResponse({'encontrado': False})

    try:
        visitante = Visitor.objects.get(document_id=document_id)
        visitas = Visit.objects.filter(visitor=visitante).order_by('-entry_time')
        ultima_visita = visitas.first()

        historial = [
            {
                'fecha': timezone.localtime(v.entry_time).strftime('%d/%m/%Y %H:%M'),
                'area': v.area
            }
            for v in visitas[:5]
        ]

        return JsonResponse({
            'encontrado': True,
            'first_name': getattr(visitante, 'first_name', ''),
            'last_name': getattr(visitante, 'last_name', ''),
            'company': getattr(visitante, 'company', ''),
            'document_type': getattr(visitante, 'document_type', 'CC'),
            'total_visitas': visitas.count(),
            'historial': historial,
            'foto': ultima_visita.photo.url if ultima_visita and ultima_visita.photo else ''
        })

    except Visitor.DoesNotExist:
        return JsonResponse({'encontrado': False})


# --- CORRECCIÓN APLICADA: Respuesta JSON con first_name y last_name ---
@login_required
def buscar_empleado(request):
    document_id = request.GET.get('document_id')

    if not document_id:
        return JsonResponse({'encontrado': False})

    try:
        empleado = Employee.objects.get(employee_id=document_id)
        permisos = EmployeePermission.objects.filter(employee=empleado).order_by('-departure_time')
        
        historial = [
            {
                'fecha': timezone.localtime(p.departure_time).strftime('%d/%m/%Y %H:%M'),
                'tipo': getattr(p, 'permit_type', 'PERSONAL')
            }
            for p in permisos[:5]
        ]

        ultima_foto = permisos.filter(photo__isnull=False).first()

        return JsonResponse({
            'encontrado': True,
            'first_name': empleado.first_name,
            'last_name': empleado.last_name,
            'area': getattr(empleado, 'area', ''),
            'company': getattr(empleado, 'company', ''),
            'document_type': getattr(empleado, 'document_type', 'cedula'),
            'total_permisos': permisos.count(),
            'historial': historial,
            'foto': ultima_foto.photo.url if ultima_foto and ultima_foto.photo else ''
        })

    except Employee.DoesNotExist:
        return JsonResponse({'encontrado': False})