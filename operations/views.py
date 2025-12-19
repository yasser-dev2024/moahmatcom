from django.shortcuts import render


def index(request):
    """
    الصفحة الرئيسية لتطبيق العمليات
    """
    return render(request, 'index.html')
