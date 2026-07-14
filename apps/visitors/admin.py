import csv
from datetime import timedelta
from io import BytesIO

from django.contrib import admin
from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from openpyxl.drawing.image import Image as ExcelImage
from openpyxl.styles import Font
import pytz

from .models import Visit, Visitor


# ==========================================
# FUNCIÓN DE CONVERSIÓN FORZADA A BOGOTÁ
# ==========================================
def get_bogota_time(dt):
    if not dt:
        return None
    # Si el objeto es "naive" (sin zona horaria), lo marcamos como UTC primero
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    # Convertimos explícitamente a la hora real de Colombia
    return dt.astimezone(pytz.timezone("America/Bogota"))


# ==========================================
# ACCIONES: EXTRAER HISTORIAL DE VISITANTES
# ==========================================

@admin.action(description="Extraer Historial Seleccionado (Archivo CSV)")
def extraer_historial_csv(modeladmin, request, queryset):
    """Exportación limpia a CSV.

    El delimitador ';' evita fallas con Excel en español y separa perfectamente
    Contratistas, Proveedores, Entrevistados y Externos.
    """
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = (
        'attachment; filename="historial_boccherini.csv"'
    )

    writer = csv.writer(response, delimiter=";")

    # Encabezados corporativos del archivo de auditoría con las nuevas columnas
    writer.writerow([
        "ID REGISTRO",
        "NOMBRES",
        "APELLIDOS",
        "TIPO DOC",
        "NRO DOCUMENTO",
        "PERFIL VISITANTE",
        "EMPRESA CORPORATIVA",
        "PERSONA A VISITAR",
        "CELULAR",
        "CONTACTO EMERGENCIA",
        "FECHA HORA INGRESO",
        "FECHA HORA SALIDA",
        "ESTADO ACTUAL",
    ])

    # Recorrido inteligente optimizando la consulta a base de datos con select_related
    for visita in queryset.select_related("visitor"):
        # Aplicamos la conversión forzada a las horas antes de escribir en el CSV
        entrada_local = get_bogota_time(visita.entry_time)
        salida_local = get_bogota_time(getattr(visita, "exit_time", None))

        writer.writerow([
            visita.id,
            visita.visitor.first_name if visita.visitor else "",
            visita.visitor.last_name if visita.visitor else "",
            # Mapeo del tipo de documento (convertido a minúsculas para mayor seguridad)
            {
                "cedula": "CC",
                "cedula_ciudadania": "CC",
                "ce": "CE",
                "cedula_extranjeria": "CE",
                "pasaporte": "PAS",
            }.get(str(getattr(visita.visitor, "document_type", "")).lower(), ""),
            getattr(visita.visitor, "document_id", "N/A"),
            f"{visita.visitor.visitor_type}" if visita.visitor else "",
            getattr(visita.visitor, "company", "Particular"),
            (
                visita.person_to_visit
                if hasattr(visita, "person_to_visit")
                else "No Asignado"
            ),
            getattr(visita.visitor, "phone_number", ""),
            getattr(visita.visitor, "emergency_contact", ""),
            entrada_local.strftime("%Y-%m-%d %H:%M") if entrada_local else "",
            (
                salida_local.strftime("%Y-%m-%d %H:%M")
                if salida_local
                else "En Instalaciones"
            ),
            (
                visita.get_status_display()
                if hasattr(visita, "get_status_display")
                else getattr(visita, "status", "")
            ),
        ])

    return response


@admin.action(description="Extraer Historial Seleccionado (Excel con Fotos)")
def extraer_historial_excel(modeladmin, request, queryset):
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = (
        'attachment; filename="historial_boccherini.xlsx"'
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Historial"

    # Se agregaron 'CELULAR' y 'CONTACTO EMERGENCIA' manteniendo la 'FOTO' al final
    encabezados = [
        "ID",
        "NOMBRES",
        "APELLIDOS",
        "TIPO DOC",
        "DOCUMENTO",
        "TIPO VISITANTE",
        "EMPRESA",
        "PERSONA A VISITAR",
        "DETALLE ADICIONAL",
        "CELULAR",
        "CONTACTO EMERGENCIA",
        "INGRESO",
        "SALIDA",
        "ESTADO",
        "FOTO",
    ]

    for col_num, encabezado in enumerate(encabezados, 1):
        celda = ws.cell(row=1, column=col_num)
        celda.value = encabezado
        celda.font = Font(bold=True)

    fila = 2

    for visita in queryset.select_related("visitor"):
        entrada_local = get_bogota_time(visita.entry_time)
        salida_local = get_bogota_time(getattr(visita, "exit_time", None))

        tipo_doc = {
            "cedula": "CC",
            "cedula_ciudadania": "CC",
            "ce": "CE",
            "cedula_extranjeria": "CE",
            "pasaporte": "PAS",
        }.get(str(getattr(visita.visitor, "document_type", "")).lower(), "")

        empresa = getattr(visita.visitor, "company", "Particular")
        if (
            visita.visitor
            and getattr(visita.visitor, "visitor_type", "") == "entrevistado"
        ):
            empresa = "NA"

        # Integración de reason_detail junto con celular y contacto de emergencia
        datos = [
            visita.id,
            visita.visitor.first_name if visita.visitor else "",
            visita.visitor.last_name if visita.visitor else "",
            tipo_doc,
            getattr(visita.visitor, "document_id", "N/A"),
            f"{visita.visitor.visitor_type}" if visita.visitor else "",
            empresa,
            (
                visita.person_to_visit
                if hasattr(visita, "person_to_visit")
                else "No Asignado"
            ),
            (
                getattr(visita, "reason_detail", "")
                if getattr(visita, "reason_detail", "")
                else ""
            ),
            getattr(visita.visitor, "phone_number", ""),
            getattr(visita.visitor, "emergency_contact", ""),
            entrada_local.strftime("%Y-%m-%d %H:%M") if entrada_local else "",
            (
                salida_local.strftime("%Y-%m-%d %H:%M")
                if salida_local
                else "En Instalaciones"
            ),
            (
                visita.get_status_display()
                if hasattr(visita, "get_status_display")
                else getattr(visita, "status", "")
            ),
        ]

        for col_num, valor in enumerate(datos, 1):
            ws.cell(row=fila, column=col_num, value=valor)

        # Debido a las 2 nuevas columnas, la foto ahora se inyecta en la columna O (posición 15)
        if hasattr(visita, "photo") and visita.photo:
            try:
                img = ExcelImage(visita.photo.path)
                img.width = 80
                img.height = 80
                ws.add_image(img, f"O{fila}")
                ws.row_dimensions[fila].height = 65
            except Exception:
                pass

        fila += 1

    # Ajuste de las dimensiones con las nuevas columnas incluidas (J y K)
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 18
    ws.column_dimensions["F"].width = 20
    ws.column_dimensions["G"].width = 25
    ws.column_dimensions["H"].width = 25
    ws.column_dimensions["I"].width = 45  # DETALLE ADICIONAL
    ws.column_dimensions["J"].width = 18  # CELULAR
    ws.column_dimensions["K"].width = 25  # CONTACTO EMERGENCIA
    ws.column_dimensions["L"].width = 20  # INGRESO
    ws.column_dimensions["M"].width = 20  # SALIDA
    ws.column_dimensions["N"].width = 18  # ESTADO
    ws.column_dimensions["O"].width = 18  # FOTO

    wb.save(response)
    return response


# ==========================================
# REGISTROS DEL ADMINISTRADOR (DJANGO ADMIN)
# ==========================================

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "document_id",
        "phone_number",
        "emergency_contact",
        "visitor_type",
    )
    list_filter = ("visitor_type",)
    search_fields = ("document_id", "last_name", "first_name")


class PeriodoFilter(admin.SimpleListFilter):
    title = "Periodo"
    parameter_name = "periodo"

    def lookups(self, request, model_admin):
        return (
            ("semana", "Última semana"),
            ("mes", "Último mes"),
        )

    def queryset(self, request, queryset):
        hoy = timezone.now()

        if self.value() == "semana":
            return queryset.filter(entry_time__gte=hoy - timedelta(days=7))

        if self.value() == "mes":
            return queryset.filter(entry_time__gte=hoy - timedelta(days=30))

        return queryset


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ("id", "visitor", "person_to_visit", "entry_time", "status")

    list_filter = (
        PeriodoFilter,
        "visitor__visitor_type",
        "status",
        "entry_time",
    )

    search_fields = (
        "visitor__first_name",
        "visitor__last_name",
        "person_to_visit",
    )

    actions = [extraer_historial_csv, extraer_historial_excel]