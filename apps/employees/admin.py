from django.contrib import admin
from .models import Employee, EmployeePermission

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'employee_id', 'area') # Añadido 'area'
    search_fields = ('name', 'employee_id', 'area')

@admin.register(EmployeePermission)
class EmployeePermissionAdmin(admin.ModelAdmin):
    list_display = ('employee', 'permit_type', 'departure_time', 'status')
    list_filter = ('status', 'permit_type')