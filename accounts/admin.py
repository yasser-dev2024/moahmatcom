from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from django.urls import path
from django.shortcuts import redirect, get_object_or_404

from .models import (
    User,
    UserProfile,
    UserDocument,
    Case,
    CaseReply,
    UserAgreement,
)


# --------------------------------------------------
# User
# --------------------------------------------------
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'phone_number',
        'account_status',
        'is_client',
        'is_lawyer',
        'is_staff',
        'send_agreement_button',
        'created_at',
    )
    list_filter = ('account_status', 'is_client', 'is_lawyer', 'is_staff')
    search_fields = ('username', 'email', 'phone_number')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-agreement/<int:user_id>/',
                self.admin_site.admin_view(self.send_agreement_view),
                name='send_user_agreement',
            ),
        ]
        return custom_urls + urls

    @admin.display(description="اتفاقية")
    def send_agreement_button(self, obj):
        return format_html(
            '<a class="button" style="background:#D4AF37;color:#000;'
            'font-weight:700;padding:6px 12px;border-radius:8px;" '
            'href="send-agreement/{}/">إرسال</a>',
            obj.id
        )

    def send_agreement_view(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        agreement_text = (
            "اتفاقية تقديم خدمات قانونية\n\n"
            "يلتزم الطرفان بما يلي:\n"
            "1) تقديم معلومات صحيحة.\n"
            "2) المحافظة على سرية البيانات.\n"
            "3) الالتزام بسداد الأتعاب المتفق عليها.\n"
            "\n"
            "بالموافقة أو التوقيع، يقر العميل قبوله التام."
        )

        UserAgreement.objects.create(
            user=user,
            agreement_text=agreement_text,
            status="sent",
            payment_required=True
        )

        user.account_status = "pending_agreement"
        user.save(update_fields=["account_status"])

        messages.success(request, f"تم إرسال الاتفاقية للمستخدم {user.username}.")
        return redirect(f"/admin/accounts/user/{user.id}/change/")


# --------------------------------------------------
# User Profile
# --------------------------------------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'national_id')
    search_fields = ('full_name', 'national_id')


# --------------------------------------------------
# User Documents
# --------------------------------------------------
@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'uploaded_at')
    search_fields = ('title',)


# --------------------------------------------------
# Inline Replies
# --------------------------------------------------
class CaseReplyInline(admin.TabularInline):
    model = CaseReply
    extra = 0
    fields = ('sender', 'message', 'is_visible_for_client', 'created_at')
    readonly_fields = ('created_at',)


# --------------------------------------------------
# Case
# --------------------------------------------------
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = (
        'case_box',
        'user',
        'status',
        'created_at',
    )
    list_filter = ('status', 'case_type')
    search_fields = ('case_number', 'title', 'user__username')
    ordering = ('-created_at',)
    inlines = [CaseReplyInline]

    @admin.display(description="القضية")
    def case_box(self, obj):
        is_new = obj.created_at >= timezone.now() - timedelta(days=1)

        last_reply = obj.replies.order_by('-created_at').first()
        has_new_reply = bool(
            last_reply and
            last_reply.created_at >= timezone.now() - timedelta(days=1)
        )

        badge = ""
        if is_new:
            badge = '<span style="background:#D4AF37;color:#000;padding:2px 8px;border-radius:10px;font-size:11px;">جديدة</span>'
        elif has_new_reply:
            badge = '<span style="background:#16a34a;color:#fff;padding:2px 8px;border-radius:10px;font-size:11px;">رد جديد</span>'

        return format_html(
            """
            <div style="line-height:1.6">
              <strong>{}</strong><br>
              <span style="color:#666">#{}</span><br>
              {}
            </div>
            """,
            obj.title,
            obj.case_number,
            badge
        )


# --------------------------------------------------
# Case Replies
# --------------------------------------------------
@admin.register(CaseReply)
class CaseReplyAdmin(admin.ModelAdmin):
    list_display = (
        'case',
        'sender',
        'short_message',
        'is_visible_for_client',
        'created_at',
    )
    list_filter = ('is_visible_for_client',)
    search_fields = ('message', 'case__case_number')
    ordering = ('-created_at',)

    @admin.display(description="الرسالة")
    def short_message(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message


# --------------------------------------------------
# User Agreements
# --------------------------------------------------
@admin.register(UserAgreement)
class UserAgreementAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'payment_status', 'sent_at')
    list_filter = ('status', 'payment_status')
    search_fields = ('user__username', 'agreement_text')
    ordering = ('-created_at',)
