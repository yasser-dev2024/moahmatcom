# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect

import uuid
import base64
from io import BytesIO

from django.core.files.base import ContentFile

from .models import UserProfile, Case, CaseReply, UserAgreement

# PDF (ReportLab)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

User = get_user_model()


# --------------------------------------------------
# مساعد: آخر اتفاقية للمستخدم (الأحدث)
# --------------------------------------------------
def _get_latest_agreement(user):
    if not user.is_authenticated:
        return None
    return user.agreements.order_by('-created_at').first()


# --------------------------------------------------
# مساعد: منع الوصول إذا الحساب معلّق (مع خيار السماح بالداشبورد)
# --------------------------------------------------
def _redirect_if_suspended(request, allow_dashboard=False):
    """
    إذا المستخدم معلّق:
    - نسمح له يدخل الداشبورد (لو allow_dashboard=True) عشان يشوف صندوق الاتفاقية.
    - ونمنع باقي الصفحات المهمة (رفع قضية/تعديل بيانات).
    """
    if request.user.is_authenticated:
        if request.user.account_status in ("pending_agreement", "payment_pending"):
            if allow_dashboard:
                return None
            latest = _get_latest_agreement(request.user)
            if latest:
                return redirect('agreement_view', token=latest.token)
            return redirect('account_suspended')
    return None


# --------------------------------------------------
# PDF Receipt Generator
# --------------------------------------------------
def _build_receipt_pdf(agreement: UserAgreement) -> ContentFile:
    """
    Generates a simple PDF receipt as ContentFile.
    Note: Arabic shaping in PDFs can require additional font/shaping libs.
    This receipt uses mostly English labels to avoid broken Arabic rendering.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    paid_at = getattr(agreement, "paid_at", None) or timezone.now()
    receipt_number = getattr(agreement, "receipt_number", "") or f"RCPT-{paid_at.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    amount = getattr(agreement, "payment_amount", None)
    if not amount:
        # fallback: if you don't have payment_amount field, show placeholder
        amount_text = "N/A"
    else:
        amount_text = f"{amount} SAR"

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(60, height - 80, "Payment Receipt")

    c.setFont("Helvetica", 11)
    c.drawString(60, height - 110, f"Receipt No: {receipt_number}")
    c.drawString(60, height - 130, f"Date: {paid_at.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(60, height - 150, f"Customer: {agreement.user.username}")
    c.drawString(60, height - 170, f"Agreement Title: {agreement.title}")

    c.drawString(60, height - 210, f"Amount: {amount_text}")
    c.drawString(60, height - 230, "Status: PAID")

    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(60, 60, "This receipt is system-generated.")

    c.showPage()
    c.save()

    pdf = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf, name=f"receipt_{agreement.user.username}_{paid_at.strftime('%Y%m%d_%H%M%S')}.pdf")


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
            is_client=True,
            account_status="active"
        )

        try:
            if request.user.is_authenticated:
                logout(request)
        except Exception:
            pass

        login(request, user)
        try:
            request.session.cycle_key()
        except Exception:
            pass

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
            try:
                if request.user.is_authenticated:
                    logout(request)
            except Exception:
                pass

            login(request, user)
            try:
                request.session.cycle_key()
            except Exception:
                pass

            if user.account_status in ("pending_agreement", "payment_pending"):
                return redirect('user_dashboard')

            return redirect('index')

        messages.error(request, 'بيانات الدخول غير صحيحة')
        return redirect('login')

    return render(request, 'accounts-templates/login.html')


# --------------------------------------------------
# Logout
# --------------------------------------------------
@require_http_methods(["GET", "POST"])
def logout_view(request):
    try:
        logout(request)
        request.session.flush()
    except Exception:
        pass
    return redirect('/')


# --------------------------------------------------
# صفحة حساب معلّق
# --------------------------------------------------
@login_required
def account_suspended(request):
    latest = _get_latest_agreement(request.user)
    return render(request, 'accounts/account_suspended.html', {
        'agreement': latest
    })


# --------------------------------------------------
# User Dashboard
# --------------------------------------------------
@login_required
def user_dashboard(request):
    """
    صفحة المستخدم – عرض البيانات والقضايا + إظهار صندوق الاتفاقية إذا الحساب معلّق
    """
    redir = _redirect_if_suspended(request, allow_dashboard=True)
    if redir:
        return redir

    profile = getattr(request.user, 'profile', None)
    cases = request.user.account_cases.all().order_by('-created_at')

    latest_agreement = _get_latest_agreement(request.user)

    return render(request, 'accounts/dashboard.html', {
        'profile': profile,
        'cases': cases,
        'documents': request.user.documents.all(),
        'now': timezone.now(),
        'agreement': latest_agreement,
    })


# --------------------------------------------------
# Profile Update
# --------------------------------------------------
@login_required
def profile_update_view(request):
    redir = _redirect_if_suspended(request)
    if redir:
        return redir

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
    redir = _redirect_if_suspended(request)
    if redir:
        return redir

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


# --------------------------------------------------
# Agreement View (Checkbox أو توقيع)
# --------------------------------------------------
@login_required
@csrf_protect
def agreement_view(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الاتفاقية.")

    if agreement.is_completed:
        if request.user.account_status != "active":
            request.user.account_status = "active"
            request.user.save(update_fields=["account_status"])
        return redirect('user_dashboard')

    if request.method == "POST":
        accept_checkbox = request.POST.get("accept_checkbox") == "on"
        signature_data = request.POST.get("signature_data", "").strip()

        if not accept_checkbox and not signature_data:
            messages.error(request, "اختر الموافقة بالمربع أو قم بالتوقيع.")
            return redirect('agreement_view', token=agreement.token)

        if accept_checkbox:
            agreement.accepted_checkbox = True
            agreement.accepted_at = timezone.now()
            agreement.status = "accepted"

        if signature_data:
            try:
                if "base64," in signature_data:
                    header, b64 = signature_data.split("base64,", 1)
                else:
                    b64 = signature_data

                decoded = base64.b64decode(b64)
                filename = f"signature_{agreement.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
                agreement.signature_image.save(filename, ContentFile(decoded), save=False)
                agreement.signed_at = timezone.now()
                agreement.status = "signed"
            except Exception:
                messages.error(request, "تعذر حفظ التوقيع. جرّب مرة أخرى.")
                return redirect('agreement_view', token=agreement.token)

        if agreement.payment_required:
            agreement.payment_status = "pending"
            agreement.status = "payment_pending"
            request.user.account_status = "payment_pending"
            request.user.save(update_fields=["account_status"])
        else:
            request.user.account_status = "active"
            request.user.save(update_fields=["account_status"])

        agreement.save()
        messages.success(request, "تم حفظ الموافقة/التوقيع بنجاح.")
        return redirect('agreement_view', token=agreement.token)

    return render(request, "accounts/agreement.html", {
        "agreement": agreement
    })


# --------------------------------------------------
# Payment Page (NEW UI + PDF Receipt + Success Page)
# --------------------------------------------------
@login_required
@csrf_protect
def payment_page(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الصفحة.")

    # لا يظهر الدفع إلا بعد موافقة/توقيع
    if agreement.status not in ("payment_pending", "paid"):
        return redirect('agreement_view', token=agreement.token)

    # لو مدفوع مسبقًا: روح لصفحة النجاح
    if agreement.status == "paid" and getattr(agreement, "payment_status", "") == "paid":
        return redirect('payment_success', token=agreement.token)

    if request.method == "POST":
        # ✅ هنا لاحقًا تربط بوابة الدفع الفعلية
        # الآن: نعتبر الدفع تم، ونولّد إيصال
        now = timezone.now()

        # إعداد بيانات إيصال (حقول اختيارية—ستُضاف في models.py)
        if not getattr(agreement, "receipt_number", None):
            agreement.receipt_number = f"RCPT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

        agreement.paid_at = now
        agreement.payment_status = "paid"
        agreement.status = "paid"

        # Generate & attach PDF (requires receipt_pdf FileField in model)
        try:
            receipt_file = _build_receipt_pdf(agreement)
            # هذا السطر يحتاج وجود receipt_pdf = FileField في UserAgreement
            agreement.receipt_pdf.save(receipt_file.name, receipt_file, save=False)
        except Exception:
            # حتى لو فشل الـ PDF ما نخرب الدفع — لكن نبلغ برسالة
            messages.warning(request, "تم الدفع، لكن تعذر توليد إيصال PDF. سنصلحها قريبًا.")

        agreement.save()

        # تفعيل الحساب
        request.user.account_status = "active"
        request.user.save(update_fields=["account_status"])

        messages.success(request, "تم الدفع بنجاح.")
        return redirect('payment_success', token=agreement.token)

    return render(request, "accounts/payment.html", {
        "agreement": agreement
    })


# --------------------------------------------------
# Payment Success Page
# --------------------------------------------------
@login_required
def payment_success(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الصفحة.")

    if agreement.status != "paid":
        return redirect('payment_page', token=agreement.token)

    # رسالة واتساب جاهزة للمحامي (نحتاج رقم المحامي محفوظ بمكان ما لاحقًا)
    # الآن: نجهز نص فقط + رابط إيصال إن توفر
    receipt_url = ""
    try:
        if getattr(agreement, "receipt_pdf", None) and agreement.receipt_pdf:
            receipt_url = agreement.receipt_pdf.url
    except Exception:
        receipt_url = ""

    whatsapp_text = f"تم دفع اتفاقية: {agreement.title} | العميل: {agreement.user.username} | رقم الإيصال: {getattr(agreement, 'receipt_number', '')}"
    if receipt_url:
        whatsapp_text += f" | إيصال: {receipt_url}"

    return render(request, "accounts/payment_success.html", {
        "agreement": agreement,
        "receipt_url": receipt_url,
        "whatsapp_text": whatsapp_text,
    })
