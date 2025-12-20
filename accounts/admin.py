from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    UserProfile,
    UserDocument,
    Case,
    CaseReply
)


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


# --------------------------------------------------
# ملف المستخدم (إكمال البيانات)
# --------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'full_name',
        'national_id',
        'created_at',
    )

    search_fields = (
        'full_name',
        'national_id',
        'user__username',
    )


# --------------------------------------------------
# الملفات المرفقة
# --------------------------------------------------
@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'uploaded_at',
    )

    search_fields = (
        'title',
        'user__username',
    )


# --------------------------------------------------
# القضايا
# --------------------------------------------------
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'created_at',
    )

    search_fields = (
        'title',
        'user__username',
    )


# --------------------------------------------------
# الردود والتواصل
# --------------------------------------------------
@admin.register(CaseReply)
class CaseReplyAdmin(admin.ModelAdmin):
    list_display = (
        'case',
        'sender',
        'created_at',
    )

    search_fields = (
        'case__title',
        'sender__username',
    )
