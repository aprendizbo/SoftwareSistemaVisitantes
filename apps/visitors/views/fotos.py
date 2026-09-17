from pathlib import Path
import mimetypes

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.views.decorators.http import require_GET


@login_required
@require_GET
def servir_foto(request, ruta):
    """
    Sirve fotografías almacenadas en MEDIA_ROOT únicamente
    a usuarios autenticados.
    """

    media_root = Path(settings.MEDIA_ROOT).resolve()
    archivo = (media_root / ruta).resolve()

    try:
        archivo.relative_to(media_root)
    except ValueError:
        raise Http404

    if not archivo.is_file():
        raise Http404

    content_type, _ = mimetypes.guess_type(archivo.name)

    if not content_type or not content_type.startswith('image/'):
        raise Http404

    return FileResponse(
        open(archivo, 'rb'),
        content_type=content_type
    )
