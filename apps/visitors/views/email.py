from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage

def enviar_alerta_email(
    asunto,
    destinatario,
    contexto,
    imagen_bytes=None,
    nombre_imagen="foto_recepcion.jpg"
):
    try:
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

            # Se ha eliminado el _subtype="jpeg" para evitar problemas en Gmail
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

            print("FOTOGRAFÍA DE RECEPCIÓN ADJUNTADA")

        # =====================================================
        # ENVÍO
        # =====================================================

        email.send(
            fail_silently=False
        )

        print(
            f"CORREO ENVIADO A: {destinatario}"
        )

    except Exception as e:
        print(
            f"ERROR ENVIANDO CORREO: {e}"
        )
        raise