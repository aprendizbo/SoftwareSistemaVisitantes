from django.core.mail import EmailMessage
from django.conf import settings


def enviar_alerta_email(
    asunto,
    cuerpo,
    destinatario,
    imagen_bytes=None,
    nombre_imagen="foto_recepcion.jpg"
):
    try:
        print(f"Intentando enviar correo a: {destinatario}")

        email = EmailMessage(
            asunto,
            cuerpo,
            settings.DEFAULT_FROM_EMAIL,
            [destinatario]
        )

        if imagen_bytes:
            email.attach(
                nombre_imagen,
                imagen_bytes,
                'image/jpeg'
            )

        email.send(fail_silently=False)

        print(f"Correo enviado a: {destinatario}")

    except Exception as e:
        print(f"ERROR ENVIANDO CORREO: {e}")
        raise