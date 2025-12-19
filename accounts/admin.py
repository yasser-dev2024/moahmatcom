from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for Custom User
    """

    model = User

    list_display = (
        'username',
        'email',
        'phone_number',
        'is_lawyer',
        'is_client',
        'is_staff',
        'is_active',
    )

    list_filter = (
        'is_lawyer',
        'is_client',
        'is_staff',
        'is_active',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'معلومات إضافية',
            {
                'fields': (
                    'phone_number',
                    'is_lawyer',
                    'is_client',
                )
            }
        ),
    )
