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
                'first_name': getattr(
                    p.employee,
                    'first_name',
                    p.employee.name if hasattr(p.employee, 'name') else ''
                ),
                'last_name': getattr(p.employee, 'last_name', ''),
                'visitor_type': 'permiso_empleado',
                'get_visitor_type_display': 'Permiso de Empleado',
                'company': 'PERSONAL INTERNO'
            },
            'employee': p.employee,
            'area': p.employee.area,
            'entry_time': p.departure_time,
            'token_qr': getattr(p, 'token_qr', None),
            'photo': p.photo
        })

    # Ordenar todo por hora de entrada
    visitas_activas.sort(key=lambda x: x.entry_time if isinstance(x, Visit) else x['entry_time'], reverse=True)

    # HISTORIAL DE ÚLTIMOS MOVIMIENTOS
    visitas_salidas = list(
        Visit.objects.filter(
            status='salido'
        ).select_related('visitor').order_by('-exit_time')[:200]
    )
    
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
                'first_name': getattr(
                    pf.employee,
                    'first_name',
                    pf.employee.name if hasattr(pf.employee, 'name') else ''
                ),
                'last_name': getattr(pf.employee, 'last_name', ''),
                'visitor_type': 'permiso_empleado',
                'get_visitor_type_display': f'Permiso {getattr(pf, "permit_type", "empleado").capitalize()}',
                'company': 'PERSONAL INTERNO'
            },
            'area': pf.employee.area,
            'exit_time': pf.return_time,
            'tipo_accion': 'Regresó'
        })
    
    # Ordenar movimientos globales
    ultimos_movimientos_lista.sort(key=lambda x: x.exit_time if hasattr(x, 'exit_time') else x['exit_time'], reverse=True)

    # 1. CAMBIO APLICADO: Paginación ahora con 10 registros
    paginator = Paginator(ultimos_movimientos_lista, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'visitas_activas': visitas_activas,
        'page_obj': page_obj,
        'en_instalaciones_count': visitas_activas_queryset.count(),
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


# =====================================
# NUEVAS VISTAS DE DETALLE
# =====================================

@login_required
def detalle_en_instalaciones(request):
    hoy = timezone.now().date()
    # Mismo filtro que en el dashboard: ingresados el día de hoy
    visitas = Visit.objects.filter(
        status='ingresado', 
        entry_time__date=hoy
    ).select_related('visitor').order_by('-entry_time')
    
    return render(
        request,
        'visitors/detalle_dashboard.html',
        {
            'titulo': 'Personal en Instalaciones',
            'registros': visitas,
            'tipo': 'visita'
        }
    )

@login_required
def detalle_visitantes_dia(request):
    hoy = timezone.now().date()
    # Excluye entrevistados
    visitas = Visit.objects.filter(
        entry_time__date=hoy
    ).exclude(
        visitor__visitor_type='entrevistado'
    ).select_related('visitor').order_by('-entry_time')
    
    return render(
        request,
        'visitors/detalle_dashboard.html',
        {
            'titulo': 'Visitantes del Día',
            'registros': visitas,
            'tipo': 'visita'
        }
    )

@login_required
def detalle_entrevistas(request):
    hoy = timezone.now().date()
    # Solo entrevistados
    visitas = Visit.objects.filter(
        visitor__visitor_type='entrevistado', 
        entry_time__date=hoy
    ).select_related('visitor').order_by('-entry_time')
    
    return render(
        request,
        'visitors/detalle_dashboard.html',
        {
            'titulo': 'Entrevistas del Día',
            'registros': visitas,
            'tipo': 'visita'
        }
    )

@login_required
def detalle_permisos(request):
    hoy = timezone.now().date()
    # Filtra los EmployeePermission activos
    permisos = EmployeePermission.objects.filter(
        status='ACTIVO', 
        departure_time__date=hoy
    ).select_related('employee').order_by('-departure_time')
    
    return render(
        request,
        'visitors/detalle_dashboard.html',
        {
            'titulo': 'Permisos Activos',
            'registros': permisos,
            'tipo': 'permiso' # Útil en el HTML para diferenciar los campos a mostrar
        }
    )   