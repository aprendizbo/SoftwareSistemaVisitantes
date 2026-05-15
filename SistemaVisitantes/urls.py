"""
URL configuration for SistemaVisitantes project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # =====================================================
    # ADMIN
    # =====================================================

    path('admin/', admin.site.urls),


    # =====================================================
    # APPS DEL PROYECTO
    # =====================================================

    path('', include('apps.dashboard.urls')),

    path('accounts/', include('apps.accounts.urls')),

    path('visitors/', include('apps.visitors.urls')),

    path('employees/', include('apps.employees.urls')),

    path('permissions/', include('apps.permissions_module.urls')),

    path('notifications/', include('apps.notifications.urls')),

    path('reports/', include('apps.reports.urls')),
]


# =========================================================
# MEDIA FILES
# =========================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )


# =========================================================
# STATIC FILES EN DESARROLLO
# =========================================================

if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )