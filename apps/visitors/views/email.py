from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from email.mime.image import MIMEImage


DOMINIO_CORPORATIVO = "@boccherini.com.co"


def enviar_alerta_email(
    asunto,
    destinatario,
    contexto,
    imagen_bytes=None,
    nombre_imagen="foto_recepcion.jpg"
):
    try:
        # =====================================================
        # VALIDACIÓN DE DESTINATARIO
        # =====================================================

        if not destinatario:
            print("ERROR ENVIANDO CORREO: destinatario vacío")
            return False

        destinatario = destinatario.strip().lower()

        try:
            validate_email(destinatario)
        except ValidationError:
            print(
                f"ERROR ENVIANDO CORREO: dirección inválida "
                f"({destinatario})"
            )
            return False

        if not destinatario.endswith(DOMINIO_CORPORATIVO):
            print(
                f"ERROR ENVIANDO CORREO: destinatario externo "
                f"bloqueado ({destinatario})"
            )
            return False

        # =====================================================
        # ENVÍO
        # =====================================================

        print(f"Intentando enviar correo a: {destinatario}")

        html_content = render_to_string(
            "emails/movimiento_visitante.html",
            contexto
        )

        texto = (
            "Notificación de movimiento.\n\n"
            "Este correo contiene información generada "
            "automáticamente por el Sistema de Control de "
            "Accesos Boccherini."
        )

        email = EmailMultiAlternatives(
            subject=asunto,
            body=texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[destinatario]
        )

        email.attach_alternative(
            html_content,
            "text/html"
        )

        # =====================================================
        # FOTO DE RECEPCIÓN
        # =====================================================

        if imagen_bytes:
            imagen = MIMEImage(imagen_bytes)

            imagen.add_header(
                "Content-ID",
                "<foto_recepcion>"
            )

            imagen.add_header(
                "Content-Disposition",
                "inline",
                filename=nombre_imagen
            )

            email.attach(imagen)

            print(
                "FOTOGRAFÍA DE RECEPCIÓN ADJUNTADA"
            )

        # =====================================================
        # ENVÍO
        # =====================================================

        email.send(
            fail_silently=False
        )

        print(
            f"CORREO ENVIADO A: {destinatario}"
        )

        return True

    except Exception as e:
        print(
            f"ERROR ENVIANDO CORREO: {e}"
        )

        # El correo no debe impedir que se complete
        # el registro del visitante o empleado.
        return False