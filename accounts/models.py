from django.db import models
from django.contrib.auth.models import AbstractUser
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
# ملف المستخدم (إكمال البيانات)
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

    # ✅ الإضافة المطلوبة: ملاحظات المحامي (تظهر للمستخدم)
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
# الردود والتواصل مع المحامي
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

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإرسال"
    )

    class Meta:
        verbose_name = "رد"
        verbose_name_plural = "الردود"

    def __str__(self):
        return f"رد على {self.case.case_number}"
