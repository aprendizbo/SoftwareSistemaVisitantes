from django import forms
from .models import Visitor, Visit


class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['document_type', 'document_id', 'first_name', 'last_name', 'company', 'visitor_type']
        labels = {
            'document_type': 'Tipo de Documento',
            'document_id': 'Número de Documento',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'company': 'Empresa',
            'visitor_type': 'Tipo de Visitante',
        }
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'document_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de identificación'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Juan'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Pérez'
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Empresa (Opcional)'
            }),
            'visitor_type': forms.Select(attrs={'class': 'form-select'}),
        }


class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['reason_type', 'reason_detail', 'person_to_visit', 'area']
        labels = {
            'reason_type': 'Motivo de Visita',
            'reason_detail': 'Detalle Adicional',
            'person_to_visit': 'Persona a Visitar',
            'area': 'Área de Destino',
        }
        widgets = {
            'reason_type': forms.Select(attrs={'class': 'form-select'}),
            'reason_detail': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Detalle adicional (opcional)'
            }),
            'person_to_visit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la persona a visitar'
            }),
            'area': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Área de destino'
            }),
        }