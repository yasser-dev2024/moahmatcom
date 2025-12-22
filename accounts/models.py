# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.utils import timezone

import uuid


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

    # --------------------------------------------------
    # حالة الحساب
    # --------------------------------------------------
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


# --------------------------------------------------
# ✅ قوالب الاتفاقيات (مكتبة الاتفاقيات)
# --------------------------------------------------
class AgreementTemplate(models.Model):
    """
    قوالب الاتفاقيات التي تُكتب مرة واحدة ثم يتم اختيارها عند إرسال اتفاقية لعميل.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان الاتفاقية"
    )

    agreement_text = models.TextField(
        verbose_name="نص الاتفاقية"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="مفعّلة"
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

    # ✅ ربط الاتفاقية المرسلة بقالب (اختياري)
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

    accepted_checkbox = models.BooleanField(
        default=False,
        verbose_name="موافقة (مربع)"
    )

    accepted_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاريخ الموافقة"
    )

    signature_image = models.ImageField(
        upload_to="agreements/signatures/",
        blank=True,
        null=True,
        verbose_name="صورة التوقيع"
    )

    signed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="تاريخ التوقيع"
    )

    payment_required = models.BooleanField(
        default=True,
        verbose_name="يتطلب دفع"
    )

    # -------------------------------
    # بيانات الدفع العامة
    # -------------------------------
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

    # ✅ هذا هو “رقم الفاتورة” الذي تريد أن يكون ثابت ويظهر للعميل
    office_invoice_number = models.CharField(
        "رقم الفاتورة (ثابت للمكتب)",
        max_length=64,
        blank=True,
        null=True,
        help_text="رقم ثابت تضعه من الأدمن ليظهر للعميل أثناء السداد."
    )

    # ✅ هذا رقم الإيصال الذي يدخله العميل بعد الدفع (إجباري عند الإرسال)
    client_payment_receipt = models.CharField(
        "رقم إيصال العميل",
        max_length=64,
        blank=True,
        null=True,
        help_text="العميل يدخل رقم الإيصال بعد السداد/التحويل."
    )

    client_paid_at = models.DateTimeField(
        "تاريخ إدخال الإيصال من العميل",
        blank=True,
        null=True
    )

    receipt_number = models.CharField(
        "رقم إيصال المكتب",
        max_length=64,
        blank=True,
        null=True,
        help_text="يولده المكتب بعد الاعتماد (اختياري)."
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

    # -------------------------------
    # ✅ بيانات سداد (SADAD) - ثابتة ولا تقبل unique
    # -------------------------------
    sadad_bill_number = models.CharField(
        "رقم فاتورة سداد (مرجعي)",
        max_length=32,
        blank=True,
        null=True,
        help_text="إن كنت تستخدم رقم سداد ثابت، اتركه هنا (لا يوجد منع تكرار)."
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

    # -------------------------------
    # حالة الاتفاقية العامة
    # -------------------------------
    status = models.CharField(
        max_length=30,
        choices=STATUS,
        default="sent",
        verbose_name="حالة الاتفاقية"
    )

    sent_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "اتفاقية"
        verbose_name_plural = "الاتفاقيات"
        ordering = ["-created_at"]

    def __str__(self):
        return f"اتفاقية {self.user.username} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(48)

        # ✅ لو تم اختيار قالب ولم يكن النص مكتوب: انسخ تلقائياً من القالب
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
