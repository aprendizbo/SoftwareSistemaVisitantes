from django.conf import settings
from django.db import models
import uuid

# --- MODELOS DE EMPLEADOS ---
class Employee(models.Model):
    DOCUMENT_CHOICES = [
        ('cedula', 'CC'),
        ('ce', 'CE'),
        ('pasaporte', 'PAS'),
    ]

    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    
    company = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Empresa"
    )
    
    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_CHOICES,
        default='cedula',
        verbose_name="Tipo de Documento"
    )
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de Documento"
    )

    area = models.CharField(
        max_length=100,
        verbose_name="Área de Trabajo",
        blank=True,
        null=True
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número Celular"
    )

    emergency_contact_name = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre Contacto de Emergencia"
    )

    emergency_contact_relationship = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Parentesco Contacto de Emergencia"
    )

    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Número de Emergencia"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

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
    
    detalle_adicional = models.TextField(blank=True, null=True, verbose_name="Detalle / Justificación")
    
    correo_notificar = models.EmailField(max_length=254, verbose_name="Correo a Notificar", blank=True, null=True)
    
    photo = models.ImageField(
        upload_to='empleados_permisos/',
        blank=True,
        null=True,
        verbose_name='Foto'
    )
    
    token_qr = models.CharField(max_length=8, editable=False, blank=True, null=True, verbose_name='Token QR')
    status = models.CharField(max_length=20, default='ACTIVO', verbose_name="Estado")

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.permit_type}"

    class Meta:
        verbose_name = "Permiso de Empleado"
        verbose_name_plural = "Permisos de Empleados"

    def save(self, *args, **kwargs):
        if not self.token_qr:
            self.token_qr = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)


# =============================================================
# SALIDAS TEMPRANAS
# =============================================================
class EarlyDeparture(models.Model):
    DOCUMENT_CHOICES = [
        ('cedula', 'CC'),
        ('ce', 'CE'),
        ('pasaporte', 'PAS'),
    ]

    employee = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Empleado"
    )

    document_type = models.CharField(
        max_length=20,
        choices=DOCUMENT_CHOICES,
        verbose_name="Tipo de Documento"
    )

    document_id = models.CharField(
        max_length=20,
        verbose_name="Número de Documento"
    )

    first_name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Apellido"
    )

    photo = models.ImageField(
        upload_to='early_departures/',
        blank=True,
        null=True,
        verbose_name="Fotografía"
    )
    
    autorizado_por = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Autorizado por"
    )

    area = models.CharField(
        max_length=100,
        verbose_name="Área de Trabajo"
    )

    company = models.CharField(
        max_length=150,
        default="BOCCHERINI S.A.S",
        verbose_name="Empresa"
    )

    departure_date = models.DateField(
        verbose_name="Fecha de Salida"
    )

    departure_time = models.TimeField(
        verbose_name="Hora de Salida"
    )

    detail = models.TextField(
        blank=True,
        null=True,
        verbose_name="Detalle / Justificación"
    )

    correo_notificar = models.EmailField(
        max_length=254,
        blank=True,
        null=True,
        verbose_name="Correo a Notificar"
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )

    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario que Registró"
    )

    class Meta:
        verbose_name = "Salida Temprana"
        verbose_name_plural = "Salidas Tempranas"
        ordering = ["-departure_date", "-departure_time"]

    def __str__(self):
        return (
            f"{self.first_name} {self.last_name} - "
            f"{self.departure_date} {self.departure_time}"
        )