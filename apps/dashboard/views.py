from django.shortcuts import render
from django.utils import timezone
from apps.visitors.models import Visit
from apps.employees.models import EmployeePermission


def dashboard(request):
    hoy = timezone.now().date()

    # === VISITANTES ===
    # Activos en instalaciones
    visitantes_dentro = Visit.objects.filter(
        status='ingresado'
    ).select_related('visitor').order_by('-entry_time')

    # Total de ingresos del día (activos + salidos)
    visitas_hoy = Visit.objects.filter(
        entry_time__date=hoy
    ).select_related('visitor')

    # Entrevistados hoy
    entrevistados_hoy = visitas_hoy.filter(
        visitor__visitor_type='entrevistado'
    ).count()

    # Últimos 8 movimientos del día para el panel lateral
    ultimos_movimientos = visitas_hoy.order_by('-entry_time')[:8]

    # Formateo de token corto para la tabla
    for visita in visitantes_dentro:
        visita.token_corto = str(visita.token_qr)[:8].upper() if visita.token_qr else "N/A"

    # === EMPLEADOS ===
    permisos_activos = EmployeePermission.objects.filter(
        status='ACTIVO'
    ).select_related('employee')

    context = {
        # Visitantes
        'visitantes_dentro': visitantes_dentro,
        'en_instalaciones_count': visitantes_dentro.count(),
        'visitantes_dia_count': visitas_hoy.count(),
        'entrevistas_count': entrevistados_hoy,
        'ultimos_movimientos': ultimos_movimientos,

        # Empleados
        'permisos_activos': permisos_activos,
        'permisos_count': permisos_activos.count(),
    }

    return render(request, 'dashboard/dashboard.html', context)