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
from django.conf import settings
from django.core.mail import mail_admins

import uuid
import base64
import logging
from urllib.parse import quote
from django.core.files.base import ContentFile

from .models import UserProfile, Case, CaseReply, UserAgreement

User = get_user_model()
logger = logging.getLogger(__name__)


# --------------------------------------------------
# Helper: Latest Agreement
# --------------------------------------------------
def _get_latest_agreement(user):
    if not user.is_authenticated:
        return None
    return user.agreements.order_by("-created_at").first()


# --------------------------------------------------
# Helper: Redirect if suspended
# --------------------------------------------------
def _redirect_if_suspended(request, allow_dashboard=False):
    """
    إذا المستخدم معلّق:
    - نسمح له بالداشبورد فقط لو allow_dashboard=True
    - غير ذلك نوجهه لآخر اتفاقية
    """
    if request.user.is_authenticated:
        if request.user.account_status in ("pending_agreement", "payment_pending"):
            if allow_dashboard:
                return None
            latest = _get_latest_agreement(request.user)
            if latest:
                return redirect("agreement_view", token=latest.token)
            return redirect("account_suspended")
    return None


# --------------------------------------------------
# Register
# --------------------------------------------------
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if not username or not password1 or not password2:
            messages.error(request, "يرجى تعبئة جميع الحقول المطلوبة")
            return redirect("register")

        if len(username) < 4:
            messages.error(request, "اسم المستخدم يجب ألا يقل عن 4 أحرف")
            return redirect("register")

        if " " in username:
            messages.error(request, "اسم المستخدم لا يجب أن يحتوي على مسافات")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "اسم المستخدم مستخدم مسبقًا")
            return redirect("register")

        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, "البريد الإلكتروني غير صالح")
                return redirect("register")
            if User.objects.filter(email=email).exists():
                messages.error(request, "البريد الإلكتروني مستخدم مسبقًا")
                return redirect("register")

        if phone_number:
            if not phone_number.isdigit():
                messages.error(request, "رقم الجوال يجب أن يحتوي على أرقام فقط")
                return redirect("register")
            if User.objects.filter(phone_number=phone_number).exists():
                messages.error(request, "رقم الجوال مستخدم مسبقًا")
                return redirect("register")

        if password1 != password2:
            messages.error(request, "كلمتا المرور غير متطابقتين")
            return redirect("register")

        if len(password1) < 8:
            messages.error(request, "كلمة المرور يجب ألا تقل عن 8 أحرف")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            phone_number=phone_number,
            is_client=True,
            account_status="active",
        )

        login(request, user)
        try:
            request.session.cycle_key()
        except Exception:
            pass

        return redirect("index")

    return render(request, "accounts-templates/register.html")


# --------------------------------------------------
# Login
# --------------------------------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "يرجى إدخال اسم المستخدم وكلمة المرور")
            return redirect("login")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            try:
                request.session.cycle_key()
            except Exception:
                pass

            if user.account_status in ("pending_agreement", "payment_pending"):
                return redirect("user_dashboard")

            return redirect("index")

        messages.error(request, "بيانات الدخول غير صحيحة")
        return redirect("login")

    return render(request, "accounts-templates/login.html")


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
    return redirect("/")


# --------------------------------------------------
# Account Suspended
# --------------------------------------------------
@login_required
def account_suspended(request):
    latest = _get_latest_agreement(request.user)
    return render(request, "accounts/account_suspended.html", {"agreement": latest})


# --------------------------------------------------
# Dashboard
# --------------------------------------------------
@login_required
def user_dashboard(request):
    redir = _redirect_if_suspended(request, allow_dashboard=True)
    if redir:
        return redir

    profile = getattr(request.user, "profile", None)
    cases = request.user.account_cases.all().order_by("-created_at")

    return render(
        request,
        "accounts/dashboard.html",
        {
            "profile": profile,
            "cases": cases,
            "documents": request.user.documents.all(),
            "now": timezone.now(),
            "agreement": _get_latest_agreement(request.user),
        },
    )


# --------------------------------------------------
# Profile Update
# --------------------------------------------------
@login_required
def profile_update_view(request):
    redir = _redirect_if_suspended(request)
    if redir:
        return redir

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.full_name = request.POST.get("full_name", "").strip()
        profile.national_id = request.POST.get("national_id", "").strip()
        profile.address = request.POST.get("address", "").strip()

        if "id_card_image" in request.FILES:
            profile.id_card_image = request.FILES["id_card_image"]

        if not profile.full_name or not profile.national_id:
            messages.error(request, "الاسم الكامل والسجل المدني مطلوبان")
            return redirect("profile_update")

        profile.save()
        messages.success(request, "تم حفظ البيانات بنجاح")
        return redirect("user_dashboard")

    return render(request, "accounts/profile_form.html", {"profile": profile})


# --------------------------------------------------
# Create Case
# --------------------------------------------------
@login_required
def case_create(request):
    redir = _redirect_if_suspended(request)
    if redir:
        return redir

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        case_type = request.POST.get("case_type", "other")

        if not title or not description:
            messages.error(request, "عنوان القضية والوصف مطلوبان")
            return redirect("case_create")

        case_number = f"CASE-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        Case.objects.create(
            user=request.user,
            case_number=case_number,
            case_type=case_type,
            title=title,
            description=description,
        )

        messages.success(request, f"تم رفع القضية بنجاح (رقمها: {case_number})")
        return redirect("user_dashboard")

    return render(request, "accounts/case_form.html")


# --------------------------------------------------
# Agreement View (🔒 مقفلة أثناء under_review)
# --------------------------------------------------
@login_required
@csrf_protect
def agreement_view(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الاتفاقية.")

    # 🔒 قفل الاتفاقية أثناء مراجعة المكتب
    if agreement.status == "under_review":
        return render(
            request,
            "accounts/agreement_locked.html",
            {"agreement": agreement},
        )

    # لو مدفوع = فعل الحساب
    if agreement.is_completed:
        if request.user.account_status != "active":
            request.user.account_status = "active"
            request.user.save(update_fields=["account_status"])
        return redirect("user_dashboard")

    if request.method == "POST":
        accept_checkbox = request.POST.get("accept_checkbox") == "on"
        signature_data = request.POST.get("signature_data", "").strip()

        if not accept_checkbox and not signature_data:
            messages.error(request, "اختر الموافقة بالمربع أو قم بالتوقيع.")
            return redirect("agreement_view", token=agreement.token)

        if accept_checkbox:
            agreement.accepted_checkbox = True
            agreement.accepted_at = timezone.now()
            agreement.status = "accepted"

        if signature_data:
            try:
                if "base64," in signature_data:
                    _, b64 = signature_data.split("base64,", 1)
                else:
                    b64 = signature_data

                decoded = base64.b64decode(b64)
                filename = f"signature_{agreement.user.username}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png"
                agreement.signature_image.save(filename, ContentFile(decoded), save=False)
                agreement.signed_at = timezone.now()
                agreement.status = "signed"
            except Exception:
                messages.error(request, "تعذر حفظ التوقيع. جرّب مرة أخرى.")
                return redirect("agreement_view", token=agreement.token)

        if agreement.payment_required:
            agreement.status = "payment_pending"
            request.user.account_status = "payment_pending"
            request.user.save(update_fields=["account_status"])
            agreement.save()
            return redirect("payment_page", token=agreement.token)

        request.user.account_status = "active"
        request.user.save(update_fields=["account_status"])
        agreement.save()

        messages.success(request, "تم حفظ الموافقة/التوقيع بنجاح.")
        return redirect("user_dashboard")

    return render(request, "accounts/agreement.html", {"agreement": agreement})


# --------------------------------------------------
# Payment Page (🔒 مسموح فقط عند payment_pending)
# --------------------------------------------------
@login_required
@csrf_protect
def payment_page(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول.")

    # 🔒 يمنع الدفع إذا كانت under_review أو غيرها
    if agreement.status != "payment_pending":
        return redirect("payment_pending_review", token=agreement.token)

    # ====== بقية كود الدفع كما هو عندك بدون أي تغيير ======

    whatsapp_phone_international = "966531991910"

    def _build_whatsapp_url(text: str) -> str:
        return f"https://wa.me/{whatsapp_phone_international}?text={quote(text)}"

    receipt_image_url = ""
    try:
        if agreement.client_receipt_image:
            receipt_image_url = request.build_absolute_uri(agreement.client_receipt_image.url)
    except Exception:
        receipt_image_url = ""

    whatsapp_text = (
        f"تم إرسال إيصال دفع جديد للمراجعة.\n"
        f"العميل: {agreement.user.username}\n"
        f"عنوان الاتفاقية: {agreement.title}\n"
        f"المبلغ: SAR {agreement.payment_amount}\n"
        f"رقم الإيصال: {agreement.client_payment_receipt or '—'}\n"
        f"صورة الإيصال: {receipt_image_url or '—'}\n"
        f"رمز الاتفاقية: {agreement.token}"
    )
    whatsapp_url = _build_whatsapp_url(whatsapp_text)

    if request.method == "POST":
        client_receipt = request.POST.get("client_payment_receipt", "").strip()
        receipt_image = request.FILES.get("client_receipt_image")

        if not client_receipt:
            messages.error(request, "رقم إيصال الدفع مطلوب ولا يمكن الإرسال بدونه.")
            return redirect("payment_page", token=agreement.token)

        if not receipt_image:
            messages.error(request, "صورة الإيصال مطلوبة. ارفع صورة واضحة ثم أعد الإرسال.")
            return redirect("payment_page", token=agreement.token)

        allowed_content_types = {"image/jpeg", "image/png", "image/webp"}
        content_type = getattr(receipt_image, "content_type", "") or ""
        if content_type not in allowed_content_types:
            messages.error(request, "صيغة الصورة غير مدعومة. استخدم JPG أو PNG أو WEBP.")
            return redirect("payment_page", token=agreement.token)

        max_size_mb = 8
        if receipt_image.size > max_size_mb * 1024 * 1024:
            messages.error(request, f"حجم الصورة كبير. الحد الأقصى {max_size_mb}MB.")
            return redirect("payment_page", token=agreement.token)

        agreement.client_payment_receipt = client_receipt
        agreement.client_paid_at = timezone.now()
        agreement.client_receipt_image = receipt_image
        agreement.status = "under_review"
        agreement.save()

        messages.success(request, "تم إرسال رقم الإيصال وصورته بنجاح. بانتظار موافقة المكتب.")
        return redirect("payment_pending_review", token=agreement.token)

    office_invoice_number = agreement.office_invoice_number or agreement.sadad_bill_number or "—"

    return render(
        request,
        "accounts/payment.html",
        {
            "agreement": agreement,
            "office_bank_name": "مصرف الراجحي",
            "office_account_name": "مكتب عبدالمجيد الزمزمي للمحاماة",
            "office_iban": "SA00 0000 0000 0000 0000 0000",
            "office_invoice_number": office_invoice_number,
            "whatsapp_text": whatsapp_text,
            "whatsapp_url": whatsapp_url,
            "receipt_image_url": receipt_image_url,
        },
    )


# --------------------------------------------------
# Payment Pending Review Page
# --------------------------------------------------
@login_required
def payment_pending_review(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول.")

    if not agreement.client_payment_receipt or not agreement.client_receipt_image:
        return redirect("payment_page", token=agreement.token)

    return render(
        request,
        "accounts/payment_pending_review.html",
        {"agreement": agreement},
    )


# --------------------------------------------------
# Payment Success
# --------------------------------------------------
@login_required
def payment_success(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الصفحة.")

    if agreement.status != "paid":
        return redirect("payment_page", token=agreement.token)

    return render(request, "accounts/payment_success.html", {"agreement": agreement})
