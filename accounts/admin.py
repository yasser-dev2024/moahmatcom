# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone
from django.contrib import messages

from .models import (
    User,
    UserProfile,
    UserDocument,
    Case,
    CaseReply,
    AgreementTemplate,
    UserAgreement
)

# --------------------------------------------------
# User Admin
# --------------------------------------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "username",
        "email",
        "phone_number",
        "is_client",
        "is_lawyer",
        "account_status",
        "is_active",
    )

    list_filter = (
        "is_client",
        "is_lawyer",
        "account_status",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "phone_number",
    )

    ordering = ("username",)


# --------------------------------------------------
# Agreement Templates
# --------------------------------------------------
@admin.register(AgreementTemplate)
class AgreementTemplateAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("title",)
    ordering = ("-created_at",)


# --------------------------------------------------
# Admin Actions
# --------------------------------------------------
@admin.action(description="📤 إرسال الاتفاقية للعميل")
def send_agreement(modeladmin, request, queryset):
    sent_count = 0

    for ag in queryset:
        if ag.status == "sent":
            continue

        ag.status = "sent"
        ag.sent_at = timezone.now()
        ag.save(update_fields=["status", "sent_at"])

        user = ag.user
        if user.account_status == "active":
            user.account_status = "pending_agreement"
            user.save(update_fields=["account_status"])

        sent_count += 1

    messages.success(
        request,
        f"تم إرسال {sent_count} اتفاقية للعميل بنجاح."
    )


@admin.action(description="✅ اعتماد الدفع (تفعيل الاتفاقية والحساب)")
def approve_payment(modeladmin, request, queryset):
    now = timezone.now()

    for ag in queryset:
        ag.status = "paid"
        ag.paid_at = now

        if not ag.receipt_number:
            ag.receipt_number = f"OFFICE-{now.strftime('%Y%m%d')}-{ag.id}"

        ag.save()

        user = ag.user
        if user.account_status != "active":
            user.account_status = "active"
            user.save(update_fields=["account_status"])


@admin.action(description="❌ رفض الدفع (إرجاعها لانتظار الدفع)")
def reject_payment(modeladmin, request, queryset):
    for ag in queryset:
        ag.status = "payment_pending"
        ag.save()


# --------------------------------------------------
# UserAgreement Admin
# --------------------------------------------------
@admin.register(UserAgreement)
class UserAgreementAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "status",
        "payment_method",
        "payment_amount",
        "client_payment_receipt",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
    )

    search_fields = (
        "user__username",
        "office_invoice_number",
        "client_payment_receipt",
        "token",
    )

    autocomplete_fields = (
        "user",
        "template",
    )

    actions = [
        send_agreement,     # ← زر إرسال الاتفاقية
        approve_payment,
        reject_payment,
    ]

    fieldsets = (
        ("العميل والقالب", {
            "fields": ("user", "template")
        }),
        ("بيانات الاتفاقية", {
            "fields": (
                "office_name",
                "office_logo",
                "title",
                "agreement_text",
            )
        }),
        ("الموافقة / التوقيع", {
            "fields": (
                "accepted_checkbox",
                "accepted_at",
                "signature_image",
                "signed_at",
            )
        }),
        ("الدفع", {
            "fields": (
                "payment_required",
                "payment_method",
                "payment_amount",
                "office_invoice_number",
                "client_payment_receipt",
                "client_receipt_image",
                "receipt_number",
                "paid_at",
                "receipt_pdf",
            )
        }),
        ("الحالة", {
            "fields": ("status", "sent_at", "created_at")
        }),
    )

    readonly_fields = (
        "sent_at",
        "created_at",
        "paid_at",
    )


# --------------------------------------------------
# Register other models
# --------------------------------------------------
admin.site.register(UserProfile)
admin.site.register(UserDocument)
admin.site.register(Case)
admin.site.register(CaseReply)
