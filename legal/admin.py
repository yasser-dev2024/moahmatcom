from django.contrib import admin
from .models import LegalService


@admin.register(LegalService)
class LegalServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "service_type", "is_active", "order")
    list_filter = ("service_type", "is_active")
    search_fields = ("title", "description")
    ordering = ("order",)

    fieldsets = (
        ("بيانات الكرت", {
            "fields": ("title", "description", "icon", "image")
        }),
        ("الإعدادات", {
            "fields": ("service_type", "is_active", "order")
        }),
    )
