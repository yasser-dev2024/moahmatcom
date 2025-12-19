"""
URL configuration for mashromoahmecom project.
"""

from django.contrib import admin
from django.urls import path, include
from operations.views import index  # الصفحة الرئيسية

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
