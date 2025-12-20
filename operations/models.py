from django.db import models
from django.conf import settings
import uuid


class Case(models.Model):
    CASE_TYPES = [
        ('civil', 'قضية مدنية'),
        ('commercial', 'قضية تجارية'),
        ('family', 'أحوال شخصية'),
        ('criminal', 'قضية جنائية'),
        ('other', 'أخرى'),
    ]

    case_number = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name="رقم القضية"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cases',
        verbose_name="المستخدم"
    )

    case_type = models.CharField(
        max_length=20,
        choices=CASE_TYPES,
        verbose_name="نوع القضية"
    )

    title = models.CharField(
        max_length=200,
        verbose_name="عنوان القضية"
    )

    description = models.TextField(
        verbose_name="تفاصيل القضية"
    )

    attachment = models.FileField(
        upload_to='cases/',
        blank=True,
        null=True,
        verbose_name="مرفقات"
    )

    status = models.CharField(
        max_length=30,
        default='جديدة',
        verbose_name="الحالة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "قضية"
        verbose_name_plural = "القضايا"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.case_number}"
