from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings 
from django.core.paginator import Paginator # Importante para el botón "Siguiente"
from apps.visitors.models import Visit
from apps.employees.models import EmployeePermission

@login_required
def dashboard(request):
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

    # 3. HISTORIAL DE ÚLTIMOS MOVIMIENTOS CON PAGINACIÓN DE 20
    visitas_salidas = list(Visit.objects.filter(status='salido').select_related('visitor').order_by('-exit_time'))
    permisos_finalizados = EmployeePermission.objects.filter(status='FINALIZADO').select_related('employee').order_by('-return_time')
    
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
    
    # Ordenar movimientos globales por fecha/hora
    ultimos_movimientos_lista.sort(key=lambda x: x.exit_time if hasattr(x, 'exit_time') else x['exit_time'], reverse=True)

    # Aplicamos Paginación: 20 registros por página
    paginator = Paginator(ultimos_movimientos_lista, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'visitas_activas': visitas_activas,
        'page_obj': page_obj,  # Reemplaza a ultimos_movimientos y contiene el control de páginas
        'en_instalaciones_count': visitas_activas_queryset.count() + permisos_activos.count(),
        'visitantes_dia_count': Visit.objects.filter(entry_time__date=hoy).count(),
        'entrevistas_count': Visit.objects.filter(visitor__visitor_type='entrevistado').count(),
        'permisos_count': permisos_activos.count(),
    }
    
    return render(request, 'visitors/dashboard.html', context)
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings 
from django.core.paginator import Paginator # Importante para el botón "Siguiente"
from apps.visitors.models import Visit
from apps.employees.models import EmployeePermission

@login_required
def dashboard(request):
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

    # 3. HISTORIAL DE ÚLTIMOS MOVIMIENTOS CON PAGINACIÓN DE 20
    visitas_salidas = list(Visit.objects.filter(status='salido').select_related('visitor').order_by('-exit_time'))
    permisos_finalizados = EmployeePermission.objects.filter(status='FINALIZADO').select_related('employee').order_by('-return_time')
    
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
    
    # Ordenar movimientos globales por fecha/hora
    ultimos_movimientos_lista.sort(key=lambda x: x.exit_time if hasattr(x, 'exit_time') else x['exit_time'], reverse=True)

    # Aplicamos Paginación: 20 registros por página
    paginator = Paginator(ultimos_movimientos_lista, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'visitas_activas': visitas_activas,
        'page_obj': page_obj,  # Reemplaza a ultimos_movimientos y contiene el control de páginas
        'en_instalaciones_count': visitas_activas_queryset.count(),
        'visitantes_dia_count': Visit.objects.filter(entry_time__date=hoy).count(),
        'entrevistas_count': Visit.objects.filter(visitor__visitor_type='entrevistado').count(),
        'permisos_count': permisos_activos.count(),
    }
    
    return render(request, 'visitors/dashboard.html', context)