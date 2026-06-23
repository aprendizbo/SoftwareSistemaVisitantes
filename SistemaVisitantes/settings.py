import os
from pathlib import Path
import dj_database_url

# =========================================================
# BASE DIR
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SECURITY
# =========================================================
SECRET_KEY = 'django-insecure-6bg$otkd2q9+yd+pqt)0+i&8ax60z4gc5f2$c+*3+)^x@!sau='
DEBUG = True

ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    '172.16.10.250',
]

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
EMAIL_HOST_USER = 'practicante.ti@boccherini.com.co'

# ----------------------------
# AQUÍ TU CONTRASEÑA DE APLICACIÓN
# (16 caracteres generados por Google)
# ----------------------------
EMAIL_HOST_PASSWORD = 'dnidwovddrzpciuc'

# ----------------------------
# CORREO QUE APARECERÁ COMO REMITENTE
# ----------------------------
DEFAULT_FROM_EMAIL = 'Sistema Control de Accesos <practicante.ti@boccherini.com.co>'

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