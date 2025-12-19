"""
URL configuration for mashromoahmecom project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# 🔴 التعديل هنا فقط
from legal.views import home as index  # الصفحة الرئيسية (تعرض الخدمات)


urlpatterns = [
    # الصفحة الرئيسية
    path('', index, name='index'),

    # Admin
    path('admin/', admin.site.urls),

    # Project Apps
    path('accounts/', include('accounts.urls')),
    path('legal/', include('legal.urls')),
    path('operations/', include('operations.urls')),
]


# --------------------------------------------------
# MEDIA & STATIC (Development Only)
# --------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )
