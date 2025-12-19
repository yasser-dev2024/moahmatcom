from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import get_user_model

User = get_user_model()


def register_view(request):
    """
    إنشاء حساب جديد
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم مسبقًا')
            return redirect('register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            phone_number=phone_number,
            is_client=True
        )

        login(request, user)
        return redirect('index')

    return render(request, 'accounts-templates/register.html')


def login_view(request):
    """
    تسجيل الدخول
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'بيانات الدخول غير صحيحة')
            return redirect('login')

    return render(request, 'accounts-templates/login.html')
