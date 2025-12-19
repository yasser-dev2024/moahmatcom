from django.contrib import admin
from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    """
    Admin configuration for Legal Cases
    """

    list_display = (
        'title',
        'client',
        'lawyer',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'client__username',
        'lawyer__username',
    )

    ordering = (
        '-created_at',
    )
