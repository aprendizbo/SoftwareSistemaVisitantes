import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

# =========================================================
# BASE DIR
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SECURITY
# =========================================================
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        'ALLOWED_HOSTS',
        '127.0.0.1,localhost,172.16.10.250'
    ).split(',')
    if host.strip()
]

CSRF_TRUSTED_ORIGINS = [
    "https://172.16.10.250:8443",
]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# =========================================================
# APPLICATIONS
# =========================================================
INSTALLED_APPS = [
    # DJANGO
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # APPS DEL PROYECTO
    'apps.accounts',
    'apps.visitors',
    'apps.employees',
    'apps.permissions_module',
    'apps.dashboard',
    'apps.notifications',
    'apps.reports',
]

# =========================================================
# MIDDLEWARE
# =========================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SistemaVisitantes.urls'

# =========================================================
# TEMPLATES
# =========================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =========================================================
# WSGI / ASGI
# =========================================================
WSGI_APPLICATION = 'SistemaVisitantes.wsgi.application'
ASGI_APPLICATION = 'SistemaVisitantes.asgi.application'

# =========================================================
# DATABASE
# =========================================================
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR}/db.sqlite3"
    )
}

# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# =========================================================
# STATIC FILES
# =========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# =========================================================
# MEDIA FILES
# =========================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =========================================================
# CONFIGURACIÓN DE CORREO
# =========================================================

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Gmail SMTP
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

# ----------------------------
# AQUÍ TU CORREO DE GOOGLE
# ----------------------------
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')

# ----------------------------
# AQUÍ TU CONTRASEÑA DE APLICACIÓN
# ----------------------------
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# ----------------------------
# CORREO QUE APARECERÁ COMO REMITENTE
# ----------------------------
DEFAULT_FROM_EMAIL = 'Sistema Control de Accesos <practicante.ti    @boccherini.com.co>'

# ----------------------------
# DESTINO DE LAS ALERTAS
# ----------------------------
CORREO_GESTION_HUMANA = 'practicante.ti@boccherini.com.co'

# =========================================================
# AUTH
# =========================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:dashboard'
LOGOUT_REDIRECT_URL = 'login'