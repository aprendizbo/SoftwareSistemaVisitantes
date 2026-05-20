import uuid
from django.db import models


class Visitor(models.Model):
    TIPO_DOC = [
        ('cedula', 'Cédula de Ciudadanía'),
        ('ce', 'Cédula de Extranjería'),
        ('pasaporte', 'Pasaporte'),
    ]
    TIPO_VIS = [
        ('entrevistado', 'Entrevistado'),
        ('proveedor', 'Proveedor'),
        ('visitante', 'Visitante Externo'),
        ('contratista', 'Contratista'),
    ]

    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellido')
    document_type = models.CharField(max_length=50, choices=TIPO_DOC, verbose_name='Tipo de Documento')
    document_id = models.CharField(max_length=50, unique=True, verbose_name='Número de Documento')
    visitor_type = models.CharField(max_length=50, choices=TIPO_VIS, verbose_name='Tipo de Visitante')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='Empresa')

    class Meta:
        verbose_name = 'Visitante'
        verbose_name_plural = 'Visitantes'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Visit(models.Model):
    # Motivos de visita separados de los permisos de empleados
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
        blank=True, null=True, verbose_name='Motivo de Visita'
    )
    person_to_visit = models.CharField(max_length=100, verbose_name='Persona a Visitar')
    reason_detail = models.TextField(blank=True, null=True, verbose_name='Detalle Adicional')
    area = models.CharField(max_length=100, verbose_name='Área de Destino')
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