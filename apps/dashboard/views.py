from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings 
from apps.visitors.models import Visit
from apps.employees.models import EmployeePermission

@login_required
def dashboard(request):
    # --- CÓDIGO DE PRUEBA (DEBUG) ---
    print("\n" + "="*50)
    print("--- RUTAS DE TEMPLATES QUE VE DJANGO ---")
    print(f"DIRS: {settings.TEMPLATES[0]['DIRS']}")
    print(f"APP_DIRS: {settings.TEMPLATES[0]['APP_DIRS']}")
    print("="*50 + "\n")
    # --------------------------------

    hoy = timezone.now().date()
    
    # 1. Traer visitas de visitantes activos
    visitas_activas_queryset = Visit.objects.filter(
        status='ingresado'
    ).select_related('visitor').order_by('-entry_time')
    
    visitas_activas = list(visitas_activas_queryset)

    # 2. Traer permisos de empleados activos
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

    # 3. Historial de Últimos Movimientos
    visitas_salidas = list(Visit.objects.filter(status='salido').select_related('visitor').order_by('-exit_time')[:10])
    permisos_finalizados = EmployeePermission.objects.filter(status='FINALIZADO').select_related('employee').order_by('-return_time')[:10]
    
    ultimos_movimientos = []

    for v in visitas_salidas:
        v.tipo_accion = 'Salió'
        ultimos_movimientos.append(v)

    for pf in permisos_finalizados:
        ultimos_movimientos.append({
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
    
    # Ordenar movimientos recientes
    ultimos_movimientos.sort(key=lambda x: x.exit_time if hasattr(x, 'exit_time') else x['exit_time'], reverse=True)

    context = {
        'visitas_activas': visitas_activas,
        'ultimos_movimientos': ultimos_movimientos[:10],
        'en_instalaciones_count': visitas_activas_queryset.count() + permisos_activos.count(),
        'visitantes_dia_count': Visit.objects.filter(entry_time__date=hoy).count(),
        'entrevistas_count': Visit.objects.filter(visitor__visitor_type='entrevistado').count(),
        'permisos_count': permisos_activos.count(),
    }
    
    return render(request, 'visitors/dashboard.html', context)  