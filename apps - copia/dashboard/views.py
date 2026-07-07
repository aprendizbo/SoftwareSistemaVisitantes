from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings 
from django.core.paginator import Paginator
from apps.visitors.models import Visit
from apps.employees.models import EmployeePermission
from datetime import timedelta

@login_required
def dashboard(request):
    # Optimización: una sola llamada a now() al inicio
    ahora = timezone.now()
    hoy = ahora.date()
    limite = ahora - timedelta(hours=24)
    
    # =====================================
    # CIERRE AUTOMÁTICO DE VISITAS Y PERMISOS (24h)
    # =====================================
    Visit.objects.filter(
        status='ingresado',
        entry_time__lt=limite
    ).update(
        status='salido',
        exit_time=ahora
    )

    EmployeePermission.objects.filter(
        status='ACTIVO',
        departure_time__lt=limite
    ).update(
        status='FINALIZADO',
        return_time=ahora
    )
    
    # Traer visitas de visitantes activos (Filtrado para el día de hoy)
    visitas_activas_queryset = Visit.objects.filter(
        status='ingresado',
        entry_time__date=hoy
    ).select_related('visitor').order_by('-entry_time')
    
    visitas_activas = list(visitas_activas_queryset)

    # Traer permisos de empleados activos
    permisos_activos = EmployeePermission.objects.filter(
        status='ACTIVO',
        departure_time__date=hoy
    ).select_related('employee')

    for p in permisos_activos:
        visitas_activas.append({
            'id': p.id,
            'is_employee_mock': True,
            'status': 'ACTIVO',
            'visitor': {
                'first_name': p.employee.name,
                'last_name': '',
                'visitor_type': 'permiso_empleado',
                'get_visitor_type_display': 'Permiso de Empleado',
                'company': 'PERSONAL INTERNO'
            },
            'area': p.employee.area,
            'entry_time': p.departure_time,
            'token_qr': p.token_qr
        })

    # Ordenar todo por hora de entrada
    visitas_activas.sort(key=lambda x: x.entry_time if isinstance(x, Visit) else x['entry_time'], reverse=True)

    # HISTORIAL DE ÚLTIMOS MOVIMIENTOS
    visitas_salidas = list(
        Visit.objects.filter(
            status='salido'
        ).select_related('visitor').order_by('-exit_time')[:200]
    )
    
    # Protección: filtramos nulos en return_time
    permisos_finalizados = EmployeePermission.objects.filter(
        status='FINALIZADO',
        return_time__isnull=False
    ).select_related('employee').order_by('-return_time')[:200]
    
    ultimos_movimientos_lista = []

    for v in visitas_salidas:
        v.tipo_accion = 'Salió'
        ultimos_movimientos_lista.append(v)

    for pf in permisos_finalizados:
        ultimos_movimientos_lista.append({
            'id': pf.id,
            'is_employee_mock': True,
            'status': 'FINALIZADO',
            'visitor': {
                'first_name': pf.employee.name,
                'last_name': '',
                'visitor_type': 'permiso_empleado',
                'get_visitor_type_display': f'Permiso {pf.permit_type.capitalize()}',
                'company': 'PERSONAL INTERNO'
            },
            'area': pf.employee.area,
            'exit_time': pf.return_time,
            'tipo_accion': 'Regresó'
        })
    
    # Ordenar movimientos globales
    ultimos_movimientos_lista.sort(key=lambda x: x.exit_time if hasattr(x, 'exit_time') else x['exit_time'], reverse=True)

    # Paginación
    paginator = Paginator(ultimos_movimientos_lista, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'visitas_activas': visitas_activas,
        'page_obj': page_obj,
        'en_instalaciones_count': visitas_activas_queryset.count(),
        
        # Ajuste: Excluye a los entrevistados del conteo general del día
        'visitantes_dia_count': Visit.objects.filter(
            entry_time__date=hoy
        ).exclude(
            visitor__visitor_type='entrevistado'
        ).count(),
        
        'entrevistas_count': Visit.objects.filter(
            visitor__visitor_type='entrevistado',
            entry_time__date=hoy
        ).count(),
        
        'permisos_count': permisos_activos.count(),
    }
    
    return render(request, 'visitors/dashboard.html', context)