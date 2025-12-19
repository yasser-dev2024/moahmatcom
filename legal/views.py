from django.shortcuts import render
from .models import LegalService


def home(request):
    """
    الصفحة الرئيسية للموقع
    تعرض الخدمات / القضايا القانونية بشكل تلقائي
    """

    services = LegalService.objects.filter(
        is_active=True
    ).order_by("order")

    return render(
        request,
        "index.html",
        {
            "services": services
        }
    )
