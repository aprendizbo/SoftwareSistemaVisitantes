from django import forms
from .models import Visitor, Visit
from apps.employees.models import EmployeePermission


class VisitorForm(forms.ModelForm):

    visitor_type = forms.ChoiceField(
        choices=[
            ('', '---------'),
            ('entrevistado', 'Entrevistado'),
            ('proveedor', 'Proveedor'),
            ('visitante_externo', 'Visitante Externo'),
            ('contratista', 'Contratista'),
            ('permiso_empleado', 'Permiso de Empleado'),
        ],
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        ),
        label='Tipo ingreso/salida'
    )

    class Meta:
        model = Visitor

        fields = [
            'first_name',
            'last_name',
            'document_type',
            'document_id',
            'phone_number',
            'emergency_contact_name',
            'emergency_contact_relationship',
            'emergency_contact_phone',
            'visitor_type',
            'company'
        ]

        labels = {
            'document_type': 'Tipo de Documento',
            'document_id': 'Número de Documento',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'phone_number': 'Número Celular',
            'emergency_contact_name': 'Nombre Contacto de Emergencia',
            'emergency_contact_relationship': 'Parentesco Contacto de Emergencia',
            'emergency_contact_phone': 'Número de Emergencia',
            'company': 'Empresa',
        }

        widgets = {
            'document_type': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'document_id': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Número de identificación'
                }
            ),

            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. Juan'
                }
            ),

            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. Pérez'
                }
            ),

            'phone_number': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. 3001234567'
                }
            ),

            'emergency_contact_name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del contacto (Opcional)'
                }
            ),

            'emergency_contact_relationship': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. Madre, Padre, Hermano (Opcional)'
                }
            ),

            'emergency_contact_phone': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ej. 3001234567 (Opcional)'
                }
            ),

            'company': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Empresa (Opcional)'
                }
            ),
        }


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
    ('Proyectos', 'Proyectos'),
    ('Gerencia', 'Gerencia'),
    ('Contabilidad', 'Contabilidad'),
    ('Tesorería', 'Tesorería'),
    ('Cartera', 'Cartera'),
    ('Jurídica', 'Jurídica'),
    ('Cafetería', 'Cafetería'),
]


class VisitForm(forms.ModelForm):

    correo_notificar = forms.EmailField(
        label='Correo a Notificar',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@boccherini.com.co'
            }
        ),
        required=True
    )

    class Meta:
        model = Visit

        fields = [
            'reason_type',
            'reason_detail',
            'person_to_visit',
            'area',
            'correo_notificar'
        ]

        labels = {
            'reason_type': 'Motivo',
            'reason_detail': 'Detalle Adicional',
            'person_to_visit': 'Responsable',
            'area': 'Área de Destino',
        }

        widgets = {
            'reason_type': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),

            'reason_detail': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 2,
                    'placeholder': 'Detalle adicional (opcional)'
                }
            ),

            'person_to_visit': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del responsable'
                }
            ),

            'area': forms.Select(
                choices=[('', '---------')] + AREA_CHOICES,
                attrs={
                    'class': 'form-select'
                }
            ),
        }

    def clean_correo_notificar(self):
        correo = self.cleaned_data.get('correo_notificar')

        if correo:
            correo = correo.strip().lower()

            if not correo.endswith('@boccherini.com.co'):
                raise forms.ValidationError(
                    'Error: Solo se permiten correos corporativos de Boccherini '
                    '(@boccherini.com.co)'
                )

        return correo


class EmployeePermissionForm(forms.ModelForm):
    permit_type = forms.ChoiceField(
        choices=EmployeePermission.PERMIT_TYPES,
        label='Tipo de Permiso',
        required=True,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    detalle_adicional = forms.CharField(
        label='Detalle / Justificación',
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Detalle adicional (opcional)'
            }
        )
    )

    correo_notificar = forms.EmailField(
        label='Correo a Notificar',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'ejemplo@boccherini.com.co'
            }
        )
    )

    class Meta:
        model = EmployeePermission
        fields = [
            'permit_type',
            'detalle_adicional',
            'correo_notificar',
        ]

    def clean_correo_notificar(self):
        correo = self.cleaned_data.get('correo_notificar')

        if correo:
            correo = correo.strip().lower()

            if not correo.endswith('@boccherini.com.co'):
                raise forms.ValidationError(
                    'Error: Solo se permiten correos corporativos de Boccherini '
                    '(@boccherini.com.co)'
                )

        return correo