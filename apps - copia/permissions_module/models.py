from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.visitors.models import Visit
# Comentado temporalmente porque el archivo models.py está vacío
# from apps.permissions_module.models import EmployeeMovement  

@login_required
def dashboard(request):
    hoy = timezone.now().date()

    # 1. Métricas de las Tarjetas Superiores
    en_instalaciones_count = Visit.objects.filter(status='ingresado').count()
    visitantes_dia_count = Visit.objects.filter(entry_time__date=hoy).count()
    
    entrevistas_count = Visit.objects.filter(
        entry_time__date=hoy, 
        visitor__visitor_type='entrevistado'
    ).count()
    
    # Lo dejamos en 0 temporalmente hasta que crees el modelo de empleados
    permisos_count = 0 

    # 2. Listados para la Tabla Principal
    visitas_activas = Visit.objects.filter(
        status='ingresado'
    ).select_related('visitor').order_by('-entry_time')

    # Lista vacía temporal para que no genere error en el template
    permisos_activos = [] 

    # 3. Últimos Movimientos (Historial Lateral)
    ultimos_movimientos = Visit.objects.filter(
        entry_time__date=hoy
    ).select_related('visitor').order_by('-entry_time')[:5]

    context = {
        'en_instalaciones_count': en_instalaciones_count,
        'visitantes_dia_count': visitantes_dia_count,
        'entrevistas_count': entrevistas_count,
        'permisos_count': permisos_count,
        'visitas_activas': visitas_activas,
        'permisos_activos': permisos_activos,
        'ultimos_movimientos': ultimos_movimientos,
    }

    return render(request, 'visitors/dashboard.html', context)