from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

User = get_user_model()


def register_view(request):
    """
    إنشاء حساب جديد مع تطبيق الشروط ومنع التكرار
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # ----------------------------
        # التحقق من الحقول المطلوبة
        # ----------------------------
        if not username or not password1 or not password2:
            messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة')
            return redirect('register')

        # ----------------------------
        # شروط اسم المستخدم
        # ----------------------------
        if len(username) < 4:
            messages.error(request, 'اسم المستخدم يجب ألا يقل عن 4 أحرف')
            return redirect('register')

        if ' ' in username:
            messages.error(request, 'اسم المستخدم لا يجب أن يحتوي على مسافات')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم مسبقًا')
            return redirect('register')

        # ----------------------------
        # التحقق من البريد الإلكتروني
        # ----------------------------
        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'البريد الإلكتروني غير صالح')
                return redirect('register')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'البريد الإلكتروني مستخدم مسبقًا')
                return redirect('register')

        # ----------------------------
        # التحقق من رقم الجوال
        # ----------------------------
        if phone_number:
            if not phone_number.isdigit():
                messages.error(request, 'رقم الجوال يجب أن يحتوي على أرقام فقط')
                return redirect('register')

            if User.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'رقم الجوال مستخدم مسبقًا')
                return redirect('register')

        # ----------------------------
        # التحقق من كلمة المرور
        # ----------------------------
        if password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
            return redirect('register')

        if len(password1) < 8:
            messages.error(request, 'كلمة المرور يجب ألا تقل عن 8 أحرف')
            return redirect('register')

        # ----------------------------
        # إنشاء المستخدم
        # ----------------------------
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
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')

        messages.error(request, 'بيانات الدخول غير صحيحة')
        return redirect('login')

    return render(request, 'accounts-templates/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    """
    تسجيل الخروج
    """
    logout(request)
    return redirect('/')
