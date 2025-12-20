from django.contrib import admin
from .models import Case


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'case_type',
        'user',
        'status',
        'created_at',
    )

    list_filter = (
        'case_type',
        'status',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'case_number',
        'user__username',
    )

    readonly_fields = (
        'case_number',
        'created_at',
    )
