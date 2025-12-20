from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .models import UserProfile, Case

User = get_user_model()


# --------------------------------------------------
# Register
# --------------------------------------------------
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

        if not username or not password1 or not password2:
            messages.error(request, 'يرجى تعبئة جميع الحقول المطلوبة')
            return redirect('register')

        if len(username) < 4:
            messages.error(request, 'اسم المستخدم يجب ألا يقل عن 4 أحرف')
            return redirect('register')

        if ' ' in username:
            messages.error(request, 'اسم المستخدم لا يجب أن يحتوي على مسافات')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم مستخدم مسبقًا')
            return redirect('register')

        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'البريد الإلكتروني غير صالح')
                return redirect('register')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'البريد الإلكتروني مستخدم مسبقًا')
                return redirect('register')

        if phone_number:
            if not phone_number.isdigit():
                messages.error(request, 'رقم الجوال يجب أن يحتوي على أرقام فقط')
                return redirect('register')

            if User.objects.filter(phone_number=phone_number).exists():
                messages.error(request, 'رقم الجوال مستخدم مسبقًا')
                return redirect('register')

        if password1 != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
            return redirect('register')

        if len(password1) < 8:
            messages.error(request, 'كلمة المرور يجب ألا تقل عن 8 أحرف')
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


# --------------------------------------------------
# Login
# --------------------------------------------------
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')
            return redirect('login')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('index')

        messages.error(request, 'بيانات الدخول غير صحيحة')
        return redirect('login')

    return render(request, 'accounts-templates/login.html')


# --------------------------------------------------
# Logout
# --------------------------------------------------
@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('/')


# --------------------------------------------------
# User Dashboard
# --------------------------------------------------
@login_required
def user_dashboard(request):
    """
    صفحة المستخدم – عرض البيانات والقضايا
    (تشمل ملاحظات المحامي المحدثة من الأدمن)
    """
    profile = getattr(request.user, 'profile', None)

    cases = request.user.account_cases.all().order_by('-created_at')

    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'cases': cases,
        'documents': request.user.documents.all(),
        'now': timezone.now(),   # ✅ لاستخدامه في تمييز الجديد بالواجهة
    })


# --------------------------------------------------
# Profile Update
# --------------------------------------------------
@login_required
def profile_update_view(request):
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':
        profile.full_name = request.POST.get('full_name', '').strip()
        profile.national_id = request.POST.get('national_id', '').strip()
        profile.address = request.POST.get('address', '').strip()

        if 'id_card_image' in request.FILES:
            profile.id_card_image = request.FILES['id_card_image']

        if not profile.full_name or not profile.national_id:
            messages.error(request, 'الاسم الكامل والسجل المدني مطلوبان')
            return redirect('profile_update')

        profile.save()
        messages.success(request, 'تم حفظ البيانات بنجاح')
        return redirect('user_dashboard')

    return render(request, 'accounts/profile_form.html', {
        'profile': profile
    })


# --------------------------------------------------
# Create Case
# --------------------------------------------------
@login_required
def case_create(request):
    """
    رفع قضية جديدة مع توليد رقم قضية تلقائي
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        case_type = request.POST.get('case_type', 'other')

        if not title or not description:
            messages.error(request, 'عنوان القضية والوصف مطلوبان')
            return redirect('case_create')

        case_number = f"CASE-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        Case.objects.create(
            user=request.user,
            case_number=case_number,
            case_type=case_type,
            title=title,
            description=description,
        )

        messages.success(request, f'تم رفع القضية بنجاح (رقمها: {case_number})')
        return redirect('user_dashboard')

    return render(request, 'accounts/case_form.html')
