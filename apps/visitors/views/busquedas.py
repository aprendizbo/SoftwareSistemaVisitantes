from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from apps.visitors.models import Visitor, Visit
from apps.employees.models import (
    Employee,
    EmployeePermission,
    EarlyDeparture,
)


@login_required
def buscar_visitante(request):
    document_id = request.GET.get('document_id')

    if not document_id:
        return JsonResponse({'encontrado': False})

    try:
        visitante = Visitor.objects.get(
            document_id=document_id
        )

        visitas = Visit.objects.filter(
            visitor=visitante
        ).order_by('-entry_time')

        ultima_visita = visitas.first()

        historial = [
            {
                'fecha': timezone.localtime(
                    v.entry_time
                ).strftime('%d/%m/%Y %H:%M'),
                'area': v.area
            }
            for v in visitas[:5]
        ]

        return JsonResponse({
            'encontrado': True,
            'first_name': getattr(
                visitante,
                'first_name',
                ''
            ),
            'last_name': getattr(
                visitante,
                'last_name',
                ''
            ),
            'company': getattr(
                visitante,
                'company',
                ''
            ),
            'document_type': getattr(
                visitante,
                'document_type',
                'cedula'
            ),
            'phone_number': getattr(
                visitante,
                'phone_number',
                ''
            ),
            'emergency_contact_name': getattr(
                visitante,
                'emergency_contact_name',
                ''
            ),
            'emergency_contact_relationship': getattr(
                visitante,
                'emergency_contact_relationship',
                ''
            ),
            'emergency_contact_phone': getattr(
                visitante,
                'emergency_contact_phone',
                ''
            ),
            'total_visitas': visitas.count(),
            'historial': historial,
            'foto': (
                ultima_visita.photo.url
                if ultima_visita
                and ultima_visita.photo
                else ''
            )
        })

    except Visitor.DoesNotExist:
        return JsonResponse({
            'encontrado': False
        })


@login_required
def buscar_empleado(request):
    document_id = request.GET.get('document_id')

    if not document_id:
        return JsonResponse({
            'encontrado': False
        })

    try:
        empleado = Employee.objects.get(
            employee_id=document_id
        )

        permisos = EmployeePermission.objects.filter(
            employee=empleado
        ).order_by('-departure_time')

        historial = [
            {
                'fecha': timezone.localtime(
                    p.departure_time
                ).strftime('%d/%m/%Y %H:%M'),
                'tipo': getattr(
                    p,
                    'permit_type',
                    'PERSONAL'
                )
            }
            for p in permisos[:5]
        ]

        # =========================================================
        # BUSCAR ÚLTIMA FOTO DEL EMPLEADO
        # =========================================================
        ultima_foto_permiso = permisos.filter(
            photo__isnull=False
        ).exclude(
            photo=''
        ).first()
        
        ultima_foto_salida = EarlyDeparture.objects.filter(
            employee=empleado,
            photo__isnull=False
        ).exclude(
            photo=''
        ).order_by(
            '-departure_date',
            '-departure_time'
        ).first()
        
        # Por defecto, ninguna foto
        foto_url = ''
        
        # Si existe foto de salida temprana, usarla
        if ultima_foto_salida and ultima_foto_salida.photo:
            foto_url = ultima_foto_salida.photo.url
        # Si existe foto de permiso y no hay foto de salida,
        # usar la del permiso
        elif ultima_foto_permiso and ultima_foto_permiso.photo:
            foto_url = ultima_foto_permiso.photo.url

        return JsonResponse({
            'encontrado': True,

            'first_name': empleado.first_name,
            'last_name': empleado.last_name,

            'area': getattr(
                empleado,
                'area',
                ''
            ),

            'company': getattr(
                empleado,
                'company',
                ''
            ),

            'document_type': getattr(
                empleado,
                'document_type',
                'cedula'
            ),

            'phone_number': getattr(
                empleado,
                'phone_number',
                ''
            ),

            'emergency_contact_name': getattr(
                empleado,
                'emergency_contact_name',
                ''
            ),

            'emergency_contact_relationship': getattr(
                empleado,
                'emergency_contact_relationship',
                ''
            ),

            'emergency_contact_phone': getattr(
                empleado,
                'emergency_contact',
                ''
            ),

            'total_permisos': permisos.count(),

            'historial': historial,

            'foto': foto_url,
        })

    except Employee.DoesNotExist:
        return JsonResponse({
            'encontrado': False
        })