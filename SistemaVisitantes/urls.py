from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ADMIN
    path('admin/', admin.site.urls),

    # AUTENTICACIÓN
    # Corregido: Apunta directo a 'registration/login.html' dentro de tu carpeta global de templates.
    # Así no movemos archivos de sitio y mantenemos la solución estable que ya te funcionaba.
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # APPS DEL PROYECTO
    path('', include('apps.dashboard.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('visitors/', include('apps.visitors.urls')),
    path('employees/', include('apps.employees.urls')),
    path('permissions/', include('apps.permissions_module.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('reports/', include('apps.reports.urls')),
]

# Configuración para archivos estáticos y media en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)