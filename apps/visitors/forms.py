from django import forms
from .models import Visitor, Visit


class VisitorForm(forms.ModelForm):
    # Declaramos el campo explícitamente para que la plantilla HTML lo dibuje normal con sus opciones originales
    visitor_type = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('entrevistado', 'Entrevistado'),
            ('proveedor', 'Proveedor'),
            ('visitante_externo', 'Visitante Externo'),
            ('contratista', 'Contratista'),
            ('permiso_empleado', 'Permiso de Empleado'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Tipo ingreso/salida'
    )

    class Meta:
        model = Visitor
        # Excluimos 'visitor_type' de los fields del modelo para evitar que salte su validador estricto de BD
        fields = ['document_type', 'document_id', 'first_name', 'last_name', 'company']
        labels = {
            'document_type': 'Tipo de Documento',
            'document_id': 'Número de Documento',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'company': 'Empresa',
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
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forzamos las opciones personalizadas en tiempo de ejecución para desvincular la validación del modelo
        self.fields['visitor_type'].choices = [
            ('', '---------'),
            ('entrevistado', 'Entrevistado'),
            ('proveedor', 'Proveedor'),
            ('visitante_externo', 'Visitante Externo'),
            ('contratista', 'Contratista'),
            ('permiso_empleado', 'Permiso de Empleado'),
        ]

    # Interceptamos la limpieza del campo para obligar a Django a aceptar "permiso_empleado" como un string válido
    def clean_visitor_type(self):
        return self.cleaned_data.get('visitor_type')


AREA_CHOICES = [
    ('Seguridad y Salud en el Trabajo', 'Seguridad y Salud en el Trabajo'),
    ('Sistema Gestión Ambiental', 'Sistema Gestión Ambiental'),
    ('Gestión Comercial', 'Gestión Comercial'),
    ('Comercio Internacional', 'Comercio Internacional'),
    ('Diseño y Desarrollo', 'Diseño y Desarrollo'),
    ('Gestión de Producción', 'Gestión de Producción'),
    ('Control de Calidad', 'Control de Calidad'),
    ('Provisión y Almacenamiento', 'Provisión y Almacenamiento'),
    ('Gestión Inventarios', 'Gestión Inventarios'),
    ('Gestión Logística', 'Gestión Logística'),
    ('Gestión de Mercadeo', 'Gestión de Mercadeo'),
    ('Gestión de Garantías', 'Gestión de Garantías'),
    ('Experiencia al Cliente', 'Experiencia al Cliente'),
    ('Gestión Humana', 'Gestión Humana'),
    ('Gestión Financiera', 'Gestión Financiera'),
    ('Gestión de Compras', 'Gestión de Compras'),
    ('Tecnologías de la Información y Comunicaciones', 'Tecnologías de la Información y Comunicaciones'),
    ('Gestión de Mantenimiento', 'Gestión de Mantenimiento'),
    ('Prevención de Pérdidas', 'Prevención de Pérdidas'),
]


# ─── CLASE ALINEADA CORRECTAMENTE AL BORDE IZQUIERDO ───
class VisitForm(forms.ModelForm):
    # Campo explícito para capturar y validar el correo de aviso en recepción
    correo_notificar = forms.EmailField(
        label='Correo a Notificar',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'ejemplo@boccherini.com.co'
        }),
        required=True
    )

    class Meta:
        model = Visit
        fields = ['reason_type', 'reason_detail', 'person_to_visit', 'area', 'correo_notificar']
        labels = {
            'reason_type': 'Motivo',
            'reason_detail': 'Detalle Adicional',
            'person_to_visit': 'Responsable',
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
                'placeholder': 'Nombre del responsable'
            }),
            'area': forms.Select(
                choices=[('', '---------')] + AREA_CHOICES,
                attrs={'class': 'form-select'}
            ),
        }

    # ─── VALIDACIÓN ESTRICTA DE DOMINIO BOCCHERINI ───
    def clean_correo_notificar(self):
        correo = self.cleaned_data.get('correo_notificar')
        if correo:
            correo = correo.strip().lower()
            if not correo.endswith('@boccherini.com.co'):
                raise forms.ValidationError("Error: Solo se permiten correos corporativos de Boccherini (@boccherini.com.co)")
        return correo