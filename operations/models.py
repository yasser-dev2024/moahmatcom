from django.db import models
from django.conf import settings


class Appointment(models.Model):
    """
    نموذج المواعيد والاجتماعات
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="المستخدم"
    )

    subject = models.CharField(
        max_length=255,
        verbose_name="موضوع الموعد"
    )

    appointment_date = models.DateTimeField(
        verbose_name="تاريخ ووقت الموعد"
    )

    notes = models.TextField(
        blank=True,
        verbose_name="ملاحظات"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )

    class Meta:
        verbose_name = "موعد"
        verbose_name_plural = "المواعيد"

    def __str__(self):
        return f"{self.subject} - {self.appointment_date}"
