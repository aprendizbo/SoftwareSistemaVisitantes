from django.shortcuts import render
from django.utils import timezone
from .models import Visita, PermisoEmpleado  # Ajusta los nombres según tus models.py

def dashboard(request):
    hoy = timezone.now().date()
    
    # 1. Filtros utilizando Django ORM
    visitantes_dentro = Visita.objects.filter(estado='DENTRO')
    visitantes_dia_total = Visita.objects.filter(hora_entrada__date=hoy).count()
    entrevistados_hoy = Visita.objects.filter(hora_entrada__date=hoy, tipo_visitor__nombre='ENTREVISTADO').count()
    permisos_activos = PermisoEmpleado.objects.filter(estado='ACTIVO')
    
    # 2. Historial reciente (Últimos 5 movimientos)
    historial_reciente = Visita.objects.all().order_by('-hora_entrada')[:5]

    # Contexto para enviar al HTML
    context = {
        'visitantes_dentro': visitantes_dentro,
        'visitantes_dentro_count': visitantes_dentro.count(),
        'visitantes_dia_total': visitantes_dia_total,
        'entrevistados_hoy': entrevistados_hoy,
        'permisos_activos': permisos_activos,
        'permisos_activos_count': permisos_activos.count(),
        'historial_reciente': historial_reciente,
    }
    
    return render(request, 'dashboard.html', context)