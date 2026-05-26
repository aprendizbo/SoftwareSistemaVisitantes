import csv
import pytz
from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from .models import Employee, EmployeePermission

# Función de conversión forzada a Bogotá
def get_bogota_time(dt):
    if not dt:
        return None
    # Si es "naive", forzamos UTC antes de convertir
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    return dt.astimezone(pytz.timezone('America/Bogota'))

@admin.action(description="Extraer Historial (CSV - Hora Colombia)")
def extraer_permisos_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="permisos_empleados_boccherini.csv"'
    
    writer = csv.writer(response, delimiter=';')
    # Encabezados
    writer.writerow([
        'ID PERMISO', 'EMPLEADO', 'TIPO DE PERMISO', 
        'HORA SALIDA', 'HORA REGRESO', 'ESTADO', 'DETALLE ADICIONAL'
    ])
    
    for p in queryset.select_related('employee'):
        # Convertimos usando la función forzada
        salida = get_bogota_time(p.departure_time)
        regreso = get_bogota_time(p.return_time)
        
        writer.writerow([
            p.id,
            p.employee.name if p.employee else 'N/A',
            p.get_permit_type_display(),
            # Usamos formato YYYY-MM-DD HH:MM para que Excel lo interprete como fecha
            salida.strftime('%Y-%m-%d %H:%M') if salida else '',
            regreso.strftime('%Y-%m-%d %H:%M') if regreso else 'Pendiente',
            p.status,
            p.detalle_adicional if p.detalle_adicional else ''
        ])
    return response

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'area')
    search_fields = ('name', 'employee_id', 'area')

@admin.register(EmployeePermission)
class EmployeePermissionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'permit_type', 'departure_time', 'return_time', 'status', 'detalle_adicional')
    list_filter = ('status', 'permit_type')
    search_fields = ('employee__name', 'detalle_adicional')
    actions = [extraer_permisos_csv]