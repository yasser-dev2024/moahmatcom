from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Admin configuration for Appointments
    """

    list_display = (
        'subject',
        'user',
        'appointment_date',
        'created_at',
    )

    list_filter = (
        'appointment_date',
    )

    search_fields = (
        'subject',
        'user__username',
    )

    ordering = (
        '-appointment_date',
    )
