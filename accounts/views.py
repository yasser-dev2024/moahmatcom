from django.shortcuts import render


def index(request):
    """
    الصفحة الرئيسية لتطبيق القضايا القانونية
    """
    return render(request, 'index.html')
