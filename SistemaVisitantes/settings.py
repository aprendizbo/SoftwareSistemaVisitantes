import os
from pathlib import Path

# =========================================================
# BASE DIR
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SECURITY
# =========================================================
SECRET_KEY = 'django-insecure-6bg$otkd2q9+yd+pqt)0+i&8ax60z4gc5f2$c+*3+)^x@!sau='
DEBUG = True
ALLOWED_HOSTS = []

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

    # APPS DEL PROYECTO (Asegúrate de que en apps.py tengan el name='apps.nombre')
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
        'DIRS': [
            BASE_DIR / 'SistemaVisitantes' / 'templates',
            BASE_DIR / 'templates',  # Por si tienes una carpeta raíz de templates globales
            BASE_DIR / 'apps' / 'dashboard' / 'templates', # Mapeo directo de seguridad para el módulo central
        ],
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
# DATABASE - POSTGRESQL
# =========================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'SistemaVisitantes',
        'USER': 'postgres',
        'PASSWORD': '1023876320',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# =========================================================
# INTERNATIONALIZATION
# =========================================================
LANGUAGE_CODE = 'es-co'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# =========================================================
# STATIC FILES (CSS, JS, Img)
# =========================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# =========================================================
# MEDIA FILES (Fotos de visitantes)
# =========================================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =========================================================
# AUTH REDIRECTS
# =========================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# =========================================================
# DEFAULT PRIMARY KEY
# =========================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py

# Si usas una cuenta SMTP real para enviar correos:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu_correo_emisor@boccherini.com.co'  # El correo que envía las alertas
EMAIL_HOST_PASSWORD = 'tu_contraseña_de_aplicacion'      # Contraseña de aplicación generada en Google

DEFAULT_FROM_EMAIL = f"Sistema Control Accesos <{EMAIL_HOST_USER}>"
CORREO_GESTION_HUMANA = 'practicante.ti@boccherini.com.co'  # La cuenta de la captura donde quieres recibirlo