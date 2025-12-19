from django.db import models
from django.conf import settings


class Case(models.Model):
    """
    نموذج القضايا القانونية
    """

    STATUS_CHOICES = [
        ('new', 'جديدة'),
        ('in_progress', 'قيد التنفيذ'),
        ('closed', 'مغلقة'),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name="عنوان القضية"
    )

    description = models.TextField(
        verbose_name="وصف القضية"
    )

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_cases',
        verbose_name="العميل"
    )

    lawyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lawyer_cases',
        verbose_name="المحامي"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="حالة القضية"
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
        verbose_name = "قضية"
        verbose_name_plural = "القضايا"

    def __str__(self):
        return self.title
