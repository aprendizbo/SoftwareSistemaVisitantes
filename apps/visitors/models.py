import uuid
from django.db import models


class Visitor(models.Model):
    TIPO_DOC = [
        ('cedula', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('pasaporte', 'Pasaporte'),
    ]
    # Se actualizó el valor de la clave 'visitante' por 'visitante_externo'
    TIPO_VIS = [
        ('entrevistado', 'Entrevistado'),
        ('proveedor', 'Proveedor'),
        ('visitante_externo', 'Visitante Externo'),
        ('contratista', 'Contratista'),
    ]

    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellido')
    document_type = models.CharField(max_length=50, choices=TIPO_DOC, verbose_name='Tipo de Documento')
    document_id = models.CharField(max_length=50, unique=True, verbose_name='Número de Documento')
    visitor_type = models.CharField(max_length=50, choices=TIPO_VIS, verbose_name='Tipo ingreso/salida')
    
    # Nuevos campos agregados
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número Celular'
    )
    emergency_contact = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Número de Emergencia'
    )
    company = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='Empresa'
    )

    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'

    @property
    def document_short(self):
        return {
            'cedula': 'CC',
            'ce': 'CE',
            'pasaporte': 'PAS',
        }.get(self.document_type, '')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Visit(models.Model):
    REASON_TYPES = [
        ('visita_general', 'Visita General'),
        ('entrega_proveedor', 'Entrega / Proveedor'),
        ('entrevista', 'Entrevista de Trabajo'),
        ('contratista', 'Trabajo de Contratista'),
        ('reunion', 'Reunión de Negocios'),
        ('otro', 'Otro'),
    ]
    STATUS = [
        ('ingresado', 'En Instalaciones'),
        ('salido', 'Salida Registrada'),
    ]

    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, verbose_name='Visitante')
    reason_type = models.CharField(
        max_length=100, choices=REASON_TYPES,
        blank=True, null=True, verbose_name='Motivo'
    )
    person_to_visit = models.CharField(max_length=100, verbose_name='Persona a Visitar')
    reason_detail = models.TextField(blank=True, null=True, verbose_name='Detalle Adicional')
    area = models.CharField(max_length=100, verbose_name='Área de Destino')
    correo_notificar = models.EmailField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='Correo a Notificar'
    )
    entry_time = models.DateTimeField(auto_now_add=True, verbose_name='Hora de Entrada')
    exit_time = models.DateTimeField(blank=True, null=True, verbose_name='Hora de Salida')
    photo = models.ImageField(upload_to='visitas_fotos/', blank=True, null=True, verbose_name='Foto')
    token_qr = models.CharField(max_length=8, unique=True, editable=False, blank=True, verbose_name='Token QR')
    status = models.CharField(max_length=20, choices=STATUS, default='ingresado', verbose_name='Estado')

    class Meta:
        verbose_name = 'Visita'
        verbose_name_plural = 'Visitas'

    def save(self, *args, **kwargs): 
        if not self.token_qr:
            self.token_qr = uuid.uuid4().hex[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.visitor.first_name} - {self.token_qr}"


# ==========================================
# NUEVOS MODELOS PARA EMPLEADOS Y PERMISOS
# ==========================================

class Employee(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellido')
    document_id = models.CharField(max_length=50, unique=True, verbose_name='Número de Documento')
    area = models.CharField(max_length=100, verbose_name='Área/Departamento')
    is_active = models.BooleanField(default=True, verbose_name='Empleado Activo')

    class Meta:
        verbose_name = 'Empleado'
        verbose_name_plural = 'Empleados'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class EmployeePermission(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Empleado')
    permit_type = models.CharField(max_length=100, verbose_name='Tipo de Permiso')
    status = models.CharField(max_length=20, default='ACTIVO', verbose_name='Estado')
    token_qr = models.CharField(max_length=8, unique=True, blank=True, verbose_name='Token QR')
    correo_notificar = models.EmailField(
        blank=True,
        null=True,
        verbose_name='Correo a Notificar'
    )

    class Meta:
        verbose_name = 'Permiso de Empleado'
        verbose_name_plural = 'Permisos de Empleados'

    def __str__(self):
        return f"{self.employee.first_name} - {self.permit_type} ({self.status})"


class EmployeeMovement(models.Model):
    STATUS_CHOICES = [
        ('ACTIVO', 'En Permiso'),
        ('FINALIZADO', 'Retornó'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, verbose_name='Empleado')
    departure_time = models.DateTimeField(auto_now_add=True, verbose_name='Hora de Salida')
    return_time = models.DateTimeField(blank=True, null=True, verbose_name='Hora de Retorno')
    reason = models.CharField(max_length=255, blank=True, null=True, verbose_name='Motivo de Salida')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVO', verbose_name='Estado')

    class Meta:
        verbose_name = 'Movimiento de Empleado'
        verbose_name_plural = 'Movimientos de Empleados'

    def __str__(self):
        return f"{self.employee.first_name} - {self.status}"

    # -------------------------------------------------------------
    # TRUCO DE COMPATIBILIDAD CON EL DASHBOARD (Duck Typing)
    # -------------------------------------------------------------
    @property
    def is_employee_mock(self):
        """Le dice al template que trate este registro como empleado"""
        return True

    @property
    def entry_time(self):
        """Mapea la hora de salida del empleado con la columna del evento"""
        return self.departure_time

    @property
    def exit_time(self):
        """Mapea el retorno"""
        return self.return_time

    @property
    def area(self):
        """Hereda el área directa del empleado"""
        return self.employee.area

    @property
    def token_qr(self):
        """Los empleados no usan QR en la tabla principal"""
        return "N/A"

    @property
    def visitor(self):
        """
        Simula un objeto 'visitor' intermedio para que llamadas como 
        visita.visitor.first_name no fallen en el template actual.
        """
        class VisitorProxy:
            def __init__(self, emp):
                self.first_name = emp.first_name
                self.last_name = emp.last_name
            def get_visitor_type_display(self):
                return "Empleado"
        return VisitorProxy(self.employee)