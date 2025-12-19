from django.db import models


class LegalService(models.Model):
    """
    أنواع القضايا والخدمات القانونية (محاماة فقط)
    """

    SERVICE_TYPES = [
        ("case", "قضية"),
        ("service", "خدمة قانونية"),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name="العنوان"
    )

    description = models.TextField(
        verbose_name="الوصف"
    )

    icon = models.CharField(
        max_length=20,
        verbose_name="الأيقونة",
        help_text="مثال: ⚖️ 🏢 👨‍👩‍👧",
        blank=True
    )

    image = models.ImageField(
        upload_to="legal_services/",
        verbose_name="صورة الكرت",
        blank=True,
        null=True
    )

    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPES,
        verbose_name="التصنيف"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="مفعل"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="الترتيب"
    )

    class Meta:
        ordering = ["order"]
        verbose_name = "خدمة قانونية / قضية"
        verbose_name_plural = "الخدمات والقضايا"

    def __str__(self):
        return self.title
