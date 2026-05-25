import base64
import io
import json
import qrcode
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.base import ContentFile
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .forms import VisitorForm, VisitForm
from .models import Visit, Visitor
from apps.employees.models import Employee, EmployeePermission

@login_required
def registrar_ingreso(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        tipo_ingreso = post_data.get('visitor_type', '')

        v_form = VisitorForm(post_data)
        vi_form = VisitForm(post_data)

        es_permiso_empleado = (tipo_ingreso == 'permiso_empleado')

        if (v_form.is_valid() or es_permiso_empleado) and vi_form.is_valid():
            
            if es_permiso_empleado:
                document_id = post_data.get('document_id')
                first_name = post_data.get('first_name', '')
                last_name = post_data.get('last_name', '')
                area_empleado = vi_form.cleaned_data.get('area', 'RECEPCION')

                empleado, _ = Employee.objects.get_or_create(
                    employee_id=document_id,
                    defaults={
                        'name': f"{first_name} {last_name}".strip(),
                        'area': area_empleado
                    }
                )

                motivo_form = vi_form.cleaned_data.get('reason_type', 'PERSONAL')
                tipo_permiso = 'LABORAL'
                if motivo_form == 'entrevista': tipo_permiso = 'MEDICINA'
                elif motivo_form == 'otro': tipo_permiso = 'PERSONAL'

                permiso = EmployeePermission.objects.create(
                    employee=empleado,
                    permit_type=tipo_permiso,
                    status='ACTIVO'
                )

                qr = qrcode.QRCode(version=1, box_size=8, border=4)
                qr.add_data(permiso.token_qr)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")

                buffer = io.BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                visit_mock = {
                    'id': permiso.id,
                    'is_employee_mock': True,
                    'visitor': {
                        'first_name': empleado.name, 
                        'last_name': '', 
                        'visitor_type': 'permiso_empleado',
                        'get_visitor_type_display': 'Permiso de Empleado',
                        'company': 'PERSONAL INTERNO'
                    },
                    'token_qr': permiso.token_qr,
                    'area': empleado.area,
                    'entry_time': permiso.departure_time,
                }

                return render(request, 'visitors/registrar_ingreso.html', {
                    'visitor_form': VisitorForm(),
                    'visit_form': VisitForm(),
                    'qr_base64': qr_base64,
                    'v_exitosa': visit_mock,
                })

            else:
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
                visit.save()

                if tipo_ingreso == 'entrevistado':
                    try:
                        asunto = f"🔔 Candidato en Recepción: {visitor_db.first_name} {visitor_db.last_name}"
                        mensaje_correo = (
                            f"Estimado equipo de Gestión Humana,\n\n"
                            f"Se informa que ha ingresado un candidato a las instalaciones.\n\n"
                            f"Atentamente,\nSistema de Control de Accesos."
                        )
                        send_mail(asunto, mensaje_correo, settings.DEFAULT_FROM_EMAIL, [settings.CORREO_GESTION_HUMANA], fail_silently=False)
                    except Exception:
                        pass

                photo_data = request.POST.get('photo_base64', '')
                if photo_data and 'base64,' in photo_data:
                    try:
                        fmt, imgstr = photo_data.split(';base64,')
                        visit.photo.save(f"visita_{visit.id}.jpg", ContentFile(base64.b64decode(imgstr)), save=True)
                    except Exception:
                        pass

                qr = qrcode.QRCode(version=1, box_size=8, border=4)
                qr.add_data(visit.token_qr)
                qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white")

                buffer = io.BytesIO()
                qr_img.save(buffer, format='PNG')
                qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                return render(request, 'visitors/registrar_ingreso.html', {
                    'visitor_form': VisitorForm(),
                    'visit_form': VisitForm(),
                    'qr_base64': qr_base64,
                    'v_exitosa': visit,
                })
        else:
            return render(request, 'visitors/registrar_ingreso.html', {'visitor_form': v_form, 'visit_form': vi_form})

    return render(request, 'visitors/registrar_ingreso.html', {'visitor_form': VisitorForm(), 'visit_form': VisitForm()})

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
            'entry_time': permiso.departure_time,
            'area': permiso.employee.area,
            'visitor': {
                'first_name': permiso.employee.name, 
                'last_name': '', 
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
            return JsonResponse({'ok': True, 'nombre': permiso.employee.name, 'token': permiso.token_qr, 'exit_time': permiso.return_time.strftime('%H:%M')})
        except EmployeePermission.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No encontrado.'}, status=404)
    else:
        try:
            visit = Visit.objects.select_related('visitor').get(id=visit_id, status='ingresado')
            visit.status = 'salido'
            visit.exit_time = timezone.now()
            visit.save()
            return JsonResponse({'ok': True, 'nombre': f"{visit.visitor.first_name}", 'token': visit.token_qr, 'exit_time': visit.exit_time.strftime('%H:%M')})
        except Visit.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'No encontrado.'}, status=404)

@login_required
def registrar_salida(request, visita_id):
    if request.method == 'POST':
        permiso_query = EmployeePermission.objects.filter(id=visita_id, status='ACTIVO')
        if permiso_query.exists():
            p = permiso_query.first()
            p.status = 'FINALIZADO'
            p.return_time = timezone.now()
            p.save()
            messages.success(request, f"Re-ingreso laboral registrado para {p.employee.name}.")
        else:
            visit = get_object_or_404(Visit, id=visita_id, status='ingresado')
            visit.status = 'salido'
            visit.exit_time = timezone.now()
            visit.save()
            messages.success(request, f"Salida registrada exitosamente para {visit.visitor.first_name} {visit.visitor.last_name}.")
    return redirect('dashboard:dashboard')

@login_required
def registrar_regreso_empleado(request, permiso_id):
    if request.method == 'POST':
        permiso = get_object_or_404(EmployeePermission, id=permiso_id, status='ACTIVO')
        permiso.status = 'FINALIZADO'
        permiso.return_time = timezone.now()
        permiso.save()
        messages.success(request, f"Re-ingreso registrado correctamente para {permiso.employee.name}.")
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