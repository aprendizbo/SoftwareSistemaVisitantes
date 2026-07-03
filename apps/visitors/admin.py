import csv
import pytz
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import Visitor, Visit

# ==========================================
# FUNCIÓN DE CONVERSIÓN FORZADA A BOGOTÁ
# ==========================================
def get_bogota_time(dt):
    if not dt:
        return None
    # Si el objeto es "naive" (sin zona horaria), lo marcamos como UTC primero
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    # Convertimos explícitamente a la hora real de Colombia
    return dt.astimezone(pytz.timezone('America/Bogota'))


# ==========================================
# ACCIÓN: EXTRAER HISTORIAL DE VISITANTES (CSV)
# ==========================================
@admin.action(description="Extraer Historial Seleccionado (Archivo CSV)")
def extraer_historial_csv(modeladmin, request, queryset):
    """
    Exportación limpia a CSV. El delimitador ';' evita fallas con Excel en español
    y separa perfectamente Contratistas, Proveedores, Entrevistados y Externos.
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="historial_boccherini.csv"'
    
    writer = csv.writer(response, delimiter=';')
    
    # Encabezados corporativos del archivo de auditoría con la nueva columna TIPO DOC
    writer.writerow([
        'ID REGISTRO', 'NOMBRES', 'APELLIDOS', 'TIPO DOC', 'NRO DOCUMENTO', 
        'PERFIL VISITANTE', 'EMPRESA CORPORATIVA', 'PERSONA A VISITAR',
        'FECHA HORA INGRESO', 'FECHA HORA SALIDA', 'ESTADO ACTUAL'
    ])
    
    # Recorrido inteligente optimizando la consulta a base de datos con select_related
    for visita in queryset.select_related('visitor'):
        # Aplicamos la conversión forzada a las horas antes de escribir en el CSV
        entrada_local = get_bogota_time(visita.entry_time)
        salida_local = get_bogota_time(getattr(visita, 'exit_time', None))
        
        writer.writerow([
            visita.id,
            visita.visitor.first_name if visita.visitor else '',
            visita.visitor.last_name if visita.visitor else '',
            
            # Mapeo del tipo de documento (convertido a minúsculas para mayor seguridad)
            {
                'cedula': 'CC',
                'cedula_ciudadania': 'CC',
                'ce': 'CE',
                'cedula_extranjeria': 'CE',
                'pasaporte': 'PAS'
            }.get(str(getattr(visita.visitor, 'document_type', '')).lower(), ''),
            
            getattr(visita.visitor, 'document_id', 'N/A'),
            visita.visitor.get_visitor_type_display() if visita.visitor else '',
            getattr(visita.visitor, 'company', 'Particular'),
            visita.person_to_visit if hasattr(visita, 'person_to_visit') else 'No Asignado',
            entrada_local.strftime('%Y-%m-%d %H:%M') if entrada_local else '',
            salida_local.strftime('%Y-%m-%d %H:%M') if salida_local else 'En Instalaciones',
            visita.get_status_display() if hasattr(visita, 'get_status_display') else getattr(visita, 'status', '')
        ])
        
    return response


# ==========================================
# REGISTROS DEL ADMINISTRADOR (DJANGO ADMIN)
# ==========================================

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'document_id', 'visitor_type')
    list_filter = ('visitor_type',)
    search_fields = ('document_id', 'last_name', 'first_name')


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    # Columnas principales para el control en portería/recepción
    list_display = ('id', 'visitor', 'person_to_visit', 'entry_time', 'status')
    
    # Filtros laterales para agrupar por Tipo de visitante, Estado y Horarios de entrada
    list_filter = ('visitor__visitor_type', 'status', 'entry_time')
    
    # Buscador veloz en barra superior
    search_fields = ('visitor__first_name', 'visitor__last_name', 'person_to_visit')
    
    # Inyección de la acción de descarga CSV para Auditoría
    actions = [extraer_historial_csv]