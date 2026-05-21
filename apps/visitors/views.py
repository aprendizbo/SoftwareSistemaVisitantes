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
from .forms import VisitorForm, VisitForm
from .models import Visit, Visitor


def dashboard(request):
    visitas_activas = Visit.objects.filter(
        status='ingresado'
    ).select_related('visitor').order_by('-entry_time')

    hoy = timezone.now().date()
    visitantes_dia = Visit.objects.filter(entry_time__date=hoy)

    ultimos_movimientos = Visit.objects.filter(
        entry_time__date=hoy
    ).select_related('visitor').order_by('-entry_time')[:10]

    context = {
        'visitas_activas': visitas_activas,
        'ultimos_movimientos': ultimos_movimientos,
        'en_instalaciones_count': visitas_activas.count(),
        'visitantes_dia_count': visitantes_dia.count(),
        'entrevistas_count': visitantes_dia.filter(
            visitor__visitor_type='entrevistado'
        ).count(),
        'permisos_count': 0,  # Se actualizará cuando integres el módulo de permisos
    }
    return render(request, 'visitors/dashboard.html', context)


def registrar_ingreso(request):
    if request.method == 'POST':
        v_form = VisitorForm(request.POST)
        vi_form = VisitForm(request.POST)

        if v_form.is_valid() and vi_form.is_valid():
            # Busca visitante existente por documento o crea uno nuevo
            visitor, created = Visitor.objects.get_or_create(
                document_id=v_form.cleaned_data['document_id'],
                defaults={
                    'first_name': v_form.cleaned_data['first_name'],
                    'last_name': v_form.cleaned_data['last_name'],
                    'document_type': v_form.cleaned_data['document_type'],
                    'visitor_type': v_form.cleaned_data['visitor_type'],
                    'company': v_form.cleaned_data.get('company', ''),
                }
            )

            # Si el visitante ya existía, actualiza sus datos
            if not created:
                visitor.first_name = v_form.cleaned_data['first_name']
                visitor.last_name = v_form.cleaned_data['last_name']
                visitor.document_type = v_form.cleaned_data['document_type']
                visitor.visitor_type = v_form.cleaned_data['visitor_type']
                visitor.company = v_form.cleaned_data.get('company', '')
                visitor.save()

            visit = vi_form.save(commit=False)
            visit.visitor = visitor
            visit.status = 'ingresado'
            visit.save()  # Aquí se genera el token_qr automáticamente

            # Guardar foto si fue capturada
            photo_data = request.POST.get('photo_base64', '')
            if photo_data and 'base64,' in photo_data:
                try:
                    fmt, imgstr = photo_data.split(';base64,')
                    visit.photo.save(
                        f"visita_{visit.id}.jpg",
                        ContentFile(base64.b64decode(imgstr)),
                        save=True
                    )
                except Exception as e:
                    pass  # La foto es opcional, no bloquea el registro

            # Generar QR con el token
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,
                border=4,
            )
            qr.add_data(visit.token_qr)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Renderizar la misma página con el modal del QR
            # NO hacemos redirect para que el contexto llegue al template
            return render(request, 'visitors/registrar_ingreso.html', {
                'visitor_form': VisitorForm(),
                'visit_form': VisitForm(),
                'qr_base64': qr_base64,
                'v_exitosa': visit,
            })

        else:
            # Formulario con errores — se lo devolvemos con los errores marcados
            return render(request, 'visitors/registrar_ingreso.html', {
                'visitor_form': v_form,
                'visit_form': vi_form,
            })

    # GET — formulario limpio
    return render(request, 'visitors/registrar_ingreso.html', {
        'visitor_form': VisitorForm(),
        'visit_form': VisitForm(),
    })


# ─────────────────────────────────────────────────────────────
# CHECKOUT
# ─────────────────────────────────────────────────────────────

def checkout_scanner(request):
    """Página principal de checkout — muestra escáner QR y búsqueda manual"""
    return render(request, 'visitors/checkout.html')


def checkout_por_token(request, token):
    """Busca una visita activa por token y muestra sus datos para confirmar checkout"""
    try:
        visit = Visit.objects.select_related('visitor').get(
            token_qr=token.upper(),
            status='ingresado'
        )
        return render(request, 'visitors/checkout.html', {
            'visit': visit,
            'confirmar': True,
        })
    except Visit.DoesNotExist:
        return render(request, 'visitors/checkout.html', {
            'error': f'Token "{token.upper()}" no encontrado o ya registró salida.',
            'confirmar': False,
        })


@require_POST
def confirmar_checkout(request, visit_id):
    """Ejecuta el checkout — cambia estado a salido y registra hora de salida"""
    try:
        visit = Visit.objects.select_related('visitor').get(
            id=visit_id,
            status='ingresado'
        )
        visit.status = 'salido'
        visit.exit_time = timezone.now()
        visit.save()

        return JsonResponse({
            'ok': True,
            'nombre': f"{visit.visitor.first_name} {visit.visitor.last_name}",
            'token': visit.token_qr,
            'exit_time': visit.exit_time.strftime('%H:%M'),
        })
    except Visit.DoesNotExist:
        return JsonResponse(
            {'ok': False, 'error': 'Visita no encontrada o ya finalizada.'},
            status=404
        )


# ─────────────────────────────────────────────────────────────
# NUEVA FUNCIÓN: REGISTRAR SALIDA DESDE TABLA DEL DASHBOARD
# ─────────────────────────────────────────────────────────────

def registrar_salida(request, visita_id):
    """Procesa la salida inmediata desde el botón del Panel Principal"""
    if request.method == 'POST':
        visit = get_object_or_404(Visit, id=visita_id, status='ingresado')
        visit.status = 'salido'
        visit.exit_time = timezone.now()
        visit.save()
        
        messages.success(request, f"Salida registrada exitosamente para {visit.visitor.first_name} {visit.visitor.last_name}.")
        
    return redirect('visitors:dashboard')