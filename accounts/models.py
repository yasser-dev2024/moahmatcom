from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinLengthValidator
from django.conf import settings
from django.utils.crypto import get_random_string

import uuid
import base64
from django.core.files.base import ContentFile


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
        ("payment_pending", "بانتظار الدفع"),
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
        ("payment_pending", "بانتظار الدفع"),
        ("paid", "تم الدفع"),
        ("expired", "منتهية"),
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

    payment_status = models.CharField(
        max_length=30,
        choices=[
            ("not_started", "لم يبدأ"),
            ("pending", "بانتظار الدفع"),
            ("paid", "تم الدفع"),
        ],
        default="not_started",
        verbose_name="حالة الدفع"
    )

    # -------------------------------
    # بيانات الدفع العامة
    # -------------------------------
    payment_amount = models.DecimalField(
        "مبلغ الدفع",
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    # ✅ رقم فاتورة المكتب/سداد الثابت الذي يظهر للعميل (يسمح بالتكرار)
    # هذا هو الرقم الموحد الذي قلت تبيه لجميع العملاء
    office_invoice_number = models.CharField(
        "رقم الفاتورة الموحد",
        max_length=32,
        blank=True,
        null=True,
        help_text="ضع رقم الفاتورة الثابت للمكتب هنا (سيظهر للعميل)."
    )

    # رقم الإيصال (بعد الدفع) يختلف من عميل لعميل (اختياري)
    receipt_number = models.CharField(
        "رقم الإيصال",
        max_length=64,
        blank=True,
        null=True
    )

    paid_at = models.DateTimeField(
        "تاريخ الدفع",
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
    # ✅ بيانات سداد (SADAD)
    # -------------------------------
    # ✅ أهم إصلاح: ممنوع unique هنا لأنك تريد رقم ثابت للجميع
    sadad_bill_number = models.CharField(
        "رقم فاتورة سداد",
        max_length=32,
        blank=True,
        null=True,
        help_text="إذا كان رقم سداد ثابت للمكتب اتركه هنا (يتكرر لجميع العملاء)."
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
