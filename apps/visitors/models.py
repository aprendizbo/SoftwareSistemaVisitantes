from django.db import models
import uuid

class Visitor(models.Model):
    TYPES = [
        ('ENTREVISTADO', 'Entrevistado'),
        ('PROVEEDOR', 'Proveedor'),
        ('EXTERNO', 'Visitante Externo'),
        ('CONTRATISTA', 'Contratista'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    document_id = models.CharField(max_length=20, unique=True)
    company = models.CharField(max_length=100, blank=True)
    visitor_type = models.CharField(max_length=20, choices=TYPES)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Visit(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE)
    reason = models.TextField()
    person_to_visit = models.CharField(max_length=100)
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    token_qr = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f"Visita de {self.visitor.first_name}"