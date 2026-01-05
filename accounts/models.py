# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils import timezone

import uuid


# --------------------------------------------------
# Helpers: upload paths
# --------------------------------------------------
def upload_client_receipt_image(instance, filename: str) -> str:
    """
    تخزين صورة إيصال العميل ضمن مسار منظم:
    media/clients/<username>/receipts/<filename>
    """
    username = "unknown"
    try:
        if instance and getattr(instance, "user", None):
            username = instance.user.username or "unknown"
    except Exception:
        username = "unknown"

    safe_filename = filename.replace("\\", "/").split("/")[-1]
    return f"clients/{username}/receipts/{safe_filename}"


# --------------------------------------------------
# المستخدم
# --------------------------------------------------
class User(AbstractUser):
    """
    Custom User Model
    الأساس لأي توسع مستقبلي (محامين – عملاء – موظفين)
    """

    email = models.EmailField(
        unique=True,
        verbose_name="البريد الإلكتروني"
    )

    phone_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="رقم الجوال"
    )

    is_lawyer = models.BooleanField(
        default=False,
        verbose_name="محامي"
    )

    is_client = models.BooleanField(
        default=False,
        verbose_name="عميل"
    )

    ACCOUNT_STATUS = [
        ("active", "مفعل"),
        ("pending_agreement", "معلّق بانتظار الاتفاقية"),
        ("payment_pending", "بانتظار الدفع/المراجعة"),
    ]

    account_status = models.CharField(
        max_length=30,
        choices=ACCOUNT_STATUS,
        default="active",
        verbose_name="حالة الحساب"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخر تحديث"
    )

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

    def __str__(self):
        return self.username


# --------------------------------------------------
# ملف المستخدم
# --------------------------------------------------
class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="المستخدم"
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="الاسم الكامل"
    )

    national_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="السجل المدني"
    )

    address = models.TextField(
        blank=True,
        null=True,
        verbose_name="العنوان الوطني"
    )

    id_card_image = models.ImageField(
        upload_to="profiles/id_cards/",
        blank=True,
        null=True,
        verbose_name="صورة الهوية"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "ملف مستخدم"
        verbose_name_plural = "ملفات المستخدمين"

    def __str__(self):
        return self.full_name or self.user.username


# --------------------------------------------------
# الملفات المرفقة للمستخدم
# --------------------------------------------------
class UserDocument(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="المستخدم"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="اسم الملف"
    )

    file = models.FileField(
        upload_to="user_documents/",
        verbose_name="الملف"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الرفع"
    )

    class Meta:
        verbose_name = "ملف مرفق"
        verbose_name_plural = "الملفات المرفقة"

    def __str__(self):
        return self.title


# --------------------------------------------------
# القضايا
# --------------------------------------------------
class Case(models.Model):

    CASE_TYPES = [
        ("civil", "مدنية"),
        ("criminal", "جنائية"),
        ("commercial", "تجارية"),
        ("family", "أحوال شخصية"),
        ("labor", "عمالية"),
        ("other", "أخرى"),
    ]

    CASE_STATUS = [
        ("new", "جديدة"),
        ("under_review", "قيد المراجعة"),
        ("in_progress", "قيد المتابعة"),
        ("closed", "مغلقة"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="account_cases",
        verbose_name="العميل"
    )

    case_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
        verbose_name="رقم القضية"
    )

    case_type = models.CharField(
        max_length=20,
        choices=CASE_TYPES,
        default="other",
        blank=True,
        verbose_name="نوع القضية"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان القضية"
    )

    description = models.TextField(
        verbose_name="وصف القضية"
    )

    status = models.CharField(
        max_length=20,
        choices=CASE_STATUS,
        default="new",
        verbose_name="حالة القضية"
    )

    lawyer_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات المحامي"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "قضية"
        verbose_name_plural = "القضايا"

    def save(self, *args, **kwargs):
        if not self.case_number:
            self.case_number = f"CASE-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.case_number


# --------------------------------------------------
# الردود
# --------------------------------------------------
class CaseReply(models.Model):
    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="القضية"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="المرسل"
    )

    message = models.TextField(
        verbose_name="الرسالة"
    )

    is_visible_for_client = models.BooleanField(
        default=True,
        verbose_name="مرئي للعميل"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )

    class Meta:
        verbose_name = "رد"
        verbose_name_plural = "الردود"
        ordering = ["created_at"]

    def __str__(self):
        return f"رد على {self.case.case_number}"


# ==================================================================
# 🟦 ماستر العملاء (الإضافة المطلوبة فقط)
# ==================================================================

class ClientMasterFolder(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="master_folder",
        verbose_name="العميل"
    )

    national_id = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="السجل المدني"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات داخلية"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "مجلد ماستر عميل"
        verbose_name_plural = "مجلدات الماستر للعملاء"

    def __str__(self):
        return f"مجلد {self.user.username}"


class ClientMasterMessage(models.Model):
    DIRECTION = [
        ("client", "من العميل"),
        ("lawyer", "من المحامي"),
    ]

    folder = models.ForeignKey(
        ClientMasterFolder,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="مجلد العميل"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="المرسل"
    )

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION,
        verbose_name="الاتجاه"
    )

    message = models.TextField(
        verbose_name="نص الرسالة"
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name="مقروءة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )

    class Meta:
        verbose_name = "رسالة ماستر"
        verbose_name_plural = "رسائل الماستر"
        ordering = ["-created_at"]

    def __str__(self):
        return f"رسالة - {self.folder.user.username}"


class ClientMasterDocument(models.Model):
    folder = models.ForeignKey(
        ClientMasterFolder,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="مجلد العميل"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="اسم المستند"
    )

    file = models.FileField(
        upload_to="clients/master_documents/",
        verbose_name="الملف"
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="تم الرفع بواسطة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الرفع"
    )

    class Meta:
        verbose_name = "مستند ماستر"
        verbose_name_plural = "مستندات الماستر"

    def __str__(self):
        return self.title


# --------------------------------------------------
# قوالب الاتفاقيات
# --------------------------------------------------
class AgreementTemplate(models.Model):
    title = models.CharField(max_length=255, verbose_name="عنوان الاتفاقية")
    agreement_text = models.TextField(verbose_name="نص الاتفاقية")
    is_active = models.BooleanField(default=True, verbose_name="مفعّلة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "قالب اتفاقية"
        verbose_name_plural = "قوالب الاتفاقيات"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# --------------------------------------------------
# الاتفاقية + الدفع + الإيصال
# --------------------------------------------------
class UserAgreement(models.Model):

    STATUS = [
        ("sent", "مرسلة"),
        ("accepted", "تمت الموافقة"),
        ("signed", "تم التوقيع"),
        ("payment_pending", "بانتظار الدفع/إرسال الإيصال"),
        ("under_review", "بانتظار مراجعة المكتب"),
        ("paid", "تم الدفع"),
        ("rejected", "مرفوض"),
        ("expired", "منتهية"),
    ]

    PAYMENT_METHOD = [
        ("sadad", "سداد (من تطبيق البنك)"),
        ("bank_transfer", "تحويل بنكي"),
        ("cash", "يدوي/نقدي"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="agreements",
        verbose_name="المستخدم"
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="agreements",
        verbose_name="القضية المرتبطة"
    )

    template = models.ForeignKey(
        AgreementTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_agreements",
        verbose_name="قالب الاتفاقية"
    )

    token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        verbose_name="رمز الوصول"
    )

    office_name = models.CharField(
        max_length=255,
        default="مكتب المحاماة والاستشارات القانونية",
        verbose_name="اسم المكتب"
    )

    office_logo = models.ImageField(
        upload_to="agreements/logos/",
        blank=True,
        null=True,
        verbose_name="شعار المكتب"
    )

    title = models.CharField(
        max_length=255,
        default="اتفاقية تقديم خدمات قانونية",
        verbose_name="عنوان الاتفاقية"
    )

    agreement_text = models.TextField(
        verbose_name="نص الاتفاقية"
    )

    accepted_checkbox = models.BooleanField(default=False, verbose_name="موافقة")
    accepted_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الموافقة")

    signature_image = models.ImageField(
        upload_to="agreements/signatures/",
        blank=True,
        null=True,
        verbose_name="صورة التوقيع"
    )

    signed_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ التوقيع")

    payment_required = models.BooleanField(default=True, verbose_name="يتطلب دفع")

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD,
        default="sadad",
        verbose_name="طريقة الدفع"
    )

    payment_amount = models.DecimalField(
        "مبلغ الدفع",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    office_invoice_number = models.CharField(
        "رقم الفاتورة (ثابت للمكتب)",
        max_length=64,
        blank=True,
        null=True
    )

    client_payment_receipt = models.CharField(
        "رقم إيصال العميل",
        max_length=64,
        blank=True,
        null=True
    )

    client_paid_at = models.DateTimeField(
        "تاريخ إدخال الإيصال من العميل",
        blank=True,
        null=True
    )

    client_receipt_image = models.ImageField(
        "صورة إيصال العميل",
        upload_to=upload_client_receipt_image,
        blank=True,
        null=True
    )

    client_receipt_image_uploaded_at = models.DateTimeField(
        "تاريخ رفع صورة الإيصال",
        blank=True,
        null=True
    )

    receipt_number = models.CharField(
        "رقم إيصال المكتب",
        max_length=64,
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        "تاريخ اعتماد الدفع",
        blank=True,
        null=True
    )

    receipt_pdf = models.FileField(
        "إيصال الدفع PDF",
        upload_to="payment_receipts/",
        blank=True,
        null=True
    )

    sadad_bill_number = models.CharField(
        "رقم فاتورة سداد (مرجعي)",
        max_length=32,
        blank=True,
        null=True
    )

    sadad_status = models.CharField(
        "حالة سداد",
        max_length=20,
        choices=[
            ("not_created", "لم تُنشأ"),
            ("pending", "بانتظار السداد"),
            ("paid", "مدفوعة"),
            ("expired", "منتهية"),
        ],
        default="not_created"
    )

    sadad_expires_at = models.DateTimeField(
        "تاريخ انتهاء سداد",
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default="sent",
        verbose_name="حالة الاتفاقية"
    )

    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "اتفاقية"
        verbose_name_plural = "الاتفاقيات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"اتفاقية {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(48)

        if self.template and (not self.agreement_text or self.agreement_text.strip() == ""):
            self.title = self.template.title
            self.agreement_text = self.template.agreement_text

        super().save(*args, **kwargs)

    @property
    def is_completed(self):
        return (
            self.status == "paid"
            or (
                not self.payment_required
                and self.status in ("accepted", "signed")
            )
        )


# ==================================================
# ✅ AUDIT + TIMELINE + SENTIMENT (إضافة شاملة للأمان والتتبع)
# ==================================================

class AuditEvent(models.Model):
    """
    سجل مركزي للأحداث:
    - تسجيل دخول/خروج
    - إنشاء/تعديل بيانات
    - رفع قضية/مرفقات
    - دفع/إيصال
    - رسائل ماستر
    - محاولات فاشلة (Rate limit / Validation)
    """
    EVENT_TYPES = [
        ("auth_login", "دخول"),
        ("auth_logout", "خروج"),
        ("auth_failed", "محاولة دخول فاشلة"),
        ("profile_update", "تحديث الملف الشخصي"),
        ("case_create", "رفع قضية"),
        ("agreement_accept", "موافقة اتفاقية"),
        ("agreement_sign", "توقيع اتفاقية"),
        ("payment_submit", "إرسال إيصال دفع"),
        ("master_message", "رسالة ماستر"),
        ("security_block", "حظر أمني"),
        ("view", "تصفح صفحة"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="المستخدم"
    )

    event_type = models.CharField(
        max_length=40,
        choices=EVENT_TYPES,
        verbose_name="نوع الحدث"
    )

    path = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="المسار"
    )

    ip = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="IP"
    )

    user_agent = models.CharField(
        max_length=300,
        blank=True,
        null=True,
        verbose_name="User-Agent"
    )

    meta = models.TextField(
        blank=True,
        null=True,
        verbose_name="بيانات إضافية"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="وقت الحدث"
    )

    class Meta:
        verbose_name = "سجل أمني"
        verbose_name_plural = "السجلات الأمنية"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.created_at}"


class CaseTimelineEvent(models.Model):
    """
    تسلسل القضية بشكل متتابع من:
    تسجيل -> رفع قضية -> جلسات -> حكم -> استئناف/خسارة/فوز
    """
    STAGES = [
        ("registered", "التسجيل"),
        ("case_submitted", "رفع القضية"),
        ("under_review", "مراجعة المكتب"),
        ("sessions", "الجلسات"),
        ("judgment", "الحكم"),
        ("appeal", "استئناف"),
        ("closed", "إغلاق"),
    ]

    OUTCOMES = [
        ("win", "كسب القضية"),
        ("lose", "خسارة"),
        ("appeal", "استئناف"),
        ("pending", "قيد المتابعة"),
    ]

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="timeline",
        verbose_name="القضية"
    )

    stage = models.CharField(
        max_length=30,
        choices=STAGES,
        verbose_name="المرحلة"
    )

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان الحدث"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="تفاصيل"
    )

    outcome = models.CharField(
        max_length=20,
        choices=OUTCOMES,
        default="pending",
        verbose_name="النتيجة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="التاريخ"
    )

    class Meta:
        verbose_name = "تسلسل قضية"
        verbose_name_plural = "تسلسل القضايا"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.case.case_number} - {self.get_stage_display()}"


class SentimentSnapshot(models.Model):
    """
    حفظ تحليل المشاعر (للعميل + للمحامي) مرتبط بالقضية أو رسالة.
    """
    TARGET = [
        ("client", "العميل"),
        ("lawyer", "المحامي"),
    ]
    LABEL = [
        ("positive", "إيجابي"),
        ("neutral", "محايد"),
        ("negative", "سلبي"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sentiments",
        verbose_name="المستخدم"
    )

    case = models.ForeignKey(
        Case,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sentiments",
        verbose_name="القضية"
    )

    target = models.CharField(
        max_length=10,
        choices=TARGET,
        verbose_name="المستهدف"
    )

    label = models.CharField(
        max_length=10,
        choices=LABEL,
        verbose_name="التصنيف"
    )

    score = models.IntegerField(
        default=0,
        verbose_name="الدرجة"
    )

    source_text = models.TextField(
        blank=True,
        null=True,
        verbose_name="النص المحلل"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="وقت التحليل"
    )

    class Meta:
        verbose_name = "تحليل مشاعر"
        verbose_name_plural = "تحليلات المشاعر"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_target_display()} - {self.get_label_display()}"
