from django.db import models
import uuid

# --- MODELOS DE EMPLEADOS ---
class Employee(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    employee_id = models.CharField(max_length=20, unique=True, verbose_name="Cédula/ID")
    area = models.CharField(max_length=100, verbose_name="Área de Trabajo", blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"


class EmployeePermission(models.Model):
    PERMIT_TYPES = [
        ('LABORAL', 'Laboral'),
        ('CALAMIDAD', 'Calamidad Doméstica'),
        ('MEDICINA', 'Medicina'),
        ('PERSONAL', 'Personal'),
    ]
    
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name="Empleado")
    permit_type = models.CharField(max_length=20, choices=PERMIT_TYPES, verbose_name="Tipo de Permiso")
    departure_time = models.DateTimeField(auto_now_add=True, verbose_name="Hora de Salida")
    return_time = models.DateTimeField(null=True, blank=True, verbose_name="Hora de Regreso")
    
    # --- CAMPO NUEVO ADAPTADO ---
    detalle_adicional = models.TextField(blank=True, null=True, verbose_name="Detalle / Justificación")
    
    # --- NUEVO CAMPO PARA NOTIFICACIONES MANUALES ---
    correo_notificar = models.EmailField(max_length=254, verbose_name="Correo a Notificar", blank=True, null=True)
    
    token_qr = models.CharField(max_length=8, unique=True, editable=False, blank=True, verbose_name='Token QR')
    status = models.CharField(max_length=20, default='ACTIVO', verbose_name="Estado")

    def __str__(self):
        return f"{self.employee.name} - {self.permit_type}"

    class Meta:
        verbose_name = "Permiso de Empleado"
        verbose_name_plural = "Permisos de Empleados"

    def save(self, *args, **kwargs):
        if not self.token_qr:
            self.token_qr = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)