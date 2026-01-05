# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_protect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required

import uuid
import base64
import logging
from urllib.parse import quote
from django.core.files.base import ContentFile

from .models import (
    UserProfile,
    Case,
    CaseReply,
    UserAgreement,
    ClientMasterFolder,
    ClientMasterMessage,
    ClientMasterDocument,
    AuditEvent,
    CaseTimelineEvent,
    SentimentSnapshot,
)

from .security import (
    validate_username,
    validate_phone,
    validate_email_safe,
    validate_safe_text,
    validate_safe_multiline,
    validate_receipt_code,
    validate_choice,
)

from .sentiment import analyze_sentiment

User = get_user_model()
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def _get_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def log_event(request, event_type: str, meta: str = ""):
    try:
        AuditEvent.objects.create(
            user=request.user if getattr(request, "user", None) and request.user.is_authenticated else None,
            event_type=event_type,
            path=request.path[:300] if request.path else "",
            ip=_get_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:300],
            meta=(meta or "")[:5000],
        )
    except Exception:
        pass


def _get_latest_agreement(user):
    if not user.is_authenticated:
        return None
    return user.agreements.order_by("-created_at").first()


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


def _ensure_master_folder_for_user(user: User):
    if not user:
        return
    if not getattr(user, "master_folder", None):
        ClientMasterFolder.objects.get_or_create(user=user)


def _case_timeline_seed(case: Case):
    if not case:
        return
    if case.timeline.exists():
        return
    CaseTimelineEvent.objects.create(
        case=case,
        stage="case_submitted",
        title="تم رفع القضية",
        description="تم استلام بيانات القضية من العميل.",
        outcome="pending",
    )
    CaseTimelineEvent.objects.create(
        case=case,
        stage="under_review",
        title="قيد مراجعة المكتب",
        description="المكتب يراجع تفاصيل القضية والمرفقات.",
        outcome="pending",
    )
    CaseTimelineEvent.objects.create(
        case=case,
        stage="sessions",
        title="مرحلة الجلسات",
        description="سيتم تحديث تفاصيل الجلسات هنا.",
        outcome="pending",
    )


def _save_sentiment(user: User, case: Case, target: str, text: str):
    try:
        res = analyze_sentiment(text or "")
        SentimentSnapshot.objects.create(
            user=user,
            case=case,
            target=target,
            label=res.label,
            score=res.score,
            source_text=(text or "")[:2000],
        )
    except Exception:
        pass


# --------------------------------------------------
# Register
# --------------------------------------------------
def register_view(request):
    if request.method == "POST":
        try:
            username = validate_username(request.POST.get("username", ""))
            email = validate_email_safe(request.POST.get("email", ""))
            phone_number = validate_phone(request.POST.get("phone_number", ""))

            password1 = request.POST.get("password1")
            password2 = request.POST.get("password2")

            if not username or not password1 or not password2:
                raise ValidationError("يرجى تعبئة جميع الحقول المطلوبة")

            if password1 != password2:
                raise ValidationError("كلمتا المرور غير متطابقتين")

            if len(password1) < 8:
                raise ValidationError("كلمة المرور يجب ألا تقل عن 8 أحرف")

            if User.objects.filter(username=username).exists():
                raise ValidationError("اسم المستخدم مستخدم مسبقًا")

            if email:
                validate_email(email)
                if User.objects.filter(email=email).exists():
                    raise ValidationError("البريد الإلكتروني مستخدم مسبقًا")

            if phone_number:
                if User.objects.filter(phone_number=phone_number).exists():
                    raise ValidationError("رقم الجوال مستخدم مسبقًا")

        except ValidationError as e:
            messages.error(request, str(e))
            log_event(request, "security_block", meta=f"register_validation:{str(e)}")
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

        _ensure_master_folder_for_user(user)
        log_event(request, "auth_login", meta="register_login")

        return redirect("index")

    return render(request, "accounts-templates/register.html")


# --------------------------------------------------
# Login
# --------------------------------------------------
def login_view(request):
    if request.method == "POST":
        try:
            username = validate_username(request.POST.get("username", ""))
            password = request.POST.get("password")

            if not username or not password:
                raise ValidationError("يرجى إدخال البيانات المطلوبة")

        except ValidationError:
            messages.error(request, "بيانات الدخول غير صحيحة")
            log_event(request, "auth_failed", meta="login_validation_failed")
            return redirect("login")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            try:
                request.session.cycle_key()
            except Exception:
                pass

            _ensure_master_folder_for_user(user)
            log_event(request, "auth_login", meta="login_success")

            if user.account_status in ("pending_agreement", "payment_pending"):
                return redirect("user_dashboard")

            return redirect("index")

        messages.error(request, "بيانات الدخول غير صحيحة")
        log_event(request, "auth_failed", meta="login_auth_failed")
        return redirect("login")

    return render(request, "accounts-templates/login.html")


# --------------------------------------------------
# Logout
# --------------------------------------------------
@require_http_methods(["GET", "POST"])
def logout_view(request):
    log_event(request, "auth_logout", meta="logout")
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
    log_event(request, "view", meta="account_suspended")
    return render(request, "accounts/account_suspended.html", {"agreement": latest})


# --------------------------------------------------
# Dashboard (✅ تم توسيعه لعرض كل معاملات المستخدم ومساراته + التقدم + المشاعر)
# --------------------------------------------------
@login_required
def user_dashboard(request):
    redir = _redirect_if_suspended(request, allow_dashboard=True)
    if redir:
        return redir

    profile = getattr(request.user, "profile", None)
    cases = request.user.account_cases.all().order_by("-created_at")

    # مستندات المستخدم
    documents = request.user.documents.all().order_by("-uploaded_at")

    # سجل المستخدم (آخر 60)
    audit_events = AuditEvent.objects.filter(user=request.user).order_by("-created_at")[:60]

    # تجهيز تقدم كل قضية (stages + latest + outcome)
    case_progress = {}
    case_sentiments = {}
    for c in cases:
        # جلب مراحل التسلسل الموجودة
        stages = list(
            c.timeline.values_list("stage", flat=True).distinct()
        )
        # التسجيل يعتبر دائمًا منجز للمستخدم (مرحلة عامة)
        if "registered" not in stages:
            stages = ["registered"] + stages

        # أحدث حدث في التسلسل
        latest = c.timeline.order_by("-created_at").first()
        latest_stage = latest.stage if latest else "case_submitted"
        latest_outcome = latest.outcome if latest else "pending"

        # أحدث حكم لو موجود
        latest_judgment = c.timeline.filter(stage="judgment").order_by("-created_at").first()
        judgment_outcome = latest_judgment.outcome if latest_judgment else ""

        case_progress[c.id] = {
            "stages": stages,
            "latest_stage": latest_stage,
            "latest_outcome": latest_outcome,
            "judgment_outcome": judgment_outcome,
        }

        # آخر تحليل مشاعر للعميل مرتبط بالقضية (آخر 1)
        s = c.sentiments.filter(target="client").order_by("-created_at").first()
        if s:
            case_sentiments[c.id] = {
                "label": s.label,
                "score": s.score,
                "created_at": s.created_at,
            }

    log_event(request, "view", meta="user_dashboard")

    return render(
        request,
        "accounts/dashboard.html",
        {
            "profile": profile,
            "cases": cases,
            "documents": documents,
            "now": timezone.now(),
            "agreement": _get_latest_agreement(request.user),
            "audit_events": audit_events,
            "case_progress": case_progress,
            "case_sentiments": case_sentiments,
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
        try:
            full_name = validate_safe_text(request.POST.get("full_name", ""), "full_name", max_len=255, min_len=2)
            national_id = validate_safe_text(request.POST.get("national_id", ""), "national_id", max_len=20, min_len=5)
            address_raw = request.POST.get("address", "").strip()
            address = ""
            if address_raw:
                address = validate_safe_multiline(address_raw, "address", max_len=1000, min_len=2)

        except ValidationError as e:
            messages.error(request, str(e))
            log_event(request, "security_block", meta=f"profile_validation:{str(e)}")
            return redirect("profile_update")

        profile.full_name = full_name
        profile.national_id = national_id
        profile.address = address

        if "id_card_image" in request.FILES:
            profile.id_card_image = request.FILES["id_card_image"]

        profile.save()
        log_event(request, "profile_update", meta="profile_updated")
        messages.success(request, "تم حفظ البيانات بنجاح")
        return redirect("user_dashboard")

    log_event(request, "view", meta="profile_update")
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
        try:
            title = validate_safe_text(request.POST.get("title", ""), "case_title", max_len=255, min_len=3)
            description = validate_safe_multiline(request.POST.get("description", ""), "case_description", max_len=3000, min_len=5)
            case_type = (request.POST.get("case_type", "other") or "other").strip()

            allowed_case_types = {"civil", "criminal", "commercial", "family", "labor", "other"}
            case_type = validate_choice(case_type, allowed_case_types, "case_type")

        except ValidationError as e:
            messages.error(request, str(e))
            log_event(request, "security_block", meta=f"case_validation:{str(e)}")
            return redirect("case_create")

        case_number = f"CASE-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        case = Case.objects.create(
            user=request.user,
            case_number=case_number,
            case_type=case_type,
            title=title,
            description=description,
        )

        _ensure_master_folder_for_user(request.user)
        _case_timeline_seed(case)

        _save_sentiment(request.user, case, "client", f"{title}\n{description}")

        log_event(request, "case_create", meta=f"case:{case.case_number}")
        messages.success(request, f"تم رفع القضية بنجاح (رقمها: {case_number})")
        return redirect("user_dashboard")

    log_event(request, "view", meta="case_create")
    return render(request, "accounts/case_form.html")


# --------------------------------------------------
# Case Timeline View
# --------------------------------------------------
@login_required
def case_timeline_view(request, case_id):
    case = get_object_or_404(Case, id=case_id)

    if case.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك.")

    timeline = case.timeline.all().order_by("created_at")
    sentiments = case.sentiments.filter(target="client").order_by("-created_at")[:5]

    log_event(request, "view", meta=f"case_timeline:{case.case_number}")

    return render(
        request,
        "accounts/case_timeline.html",
        {
            "case": case,
            "timeline": timeline,
            "client_sentiments": sentiments,
        },
    )


# --------------------------------------------------
# Agreement View
# --------------------------------------------------
@login_required
@csrf_protect
def agreement_view(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول لهذه الاتفاقية.")

    if agreement.status == "under_review":
        log_event(request, "view", meta="agreement_locked")
        return render(request, "accounts/agreement_locked.html", {"agreement": agreement})

    if agreement.is_completed:
        if request.user.account_status != "active":
            request.user.account_status = "active"
            request.user.save(update_fields=["account_status"])
        return redirect("user_dashboard")

    if request.method == "POST":
        accept_checkbox = request.POST.get("accept_checkbox") == "on"
        signature_data = (request.POST.get("signature_data", "") or "").strip()

        if signature_data:
            if "base64," in signature_data:
                _, b64 = signature_data.split("base64,", 1)
            else:
                b64 = signature_data

            cleaned = b64.replace("+", "").replace("/", "").replace("=", "")
            try:
                validate_safe_text(cleaned, "signature_base64", max_len=200000, min_len=20)
            except ValidationError:
                messages.error(request, "بيانات التوقيع غير صالحة.")
                log_event(request, "security_block", meta="signature_invalid")
                return redirect("agreement_view", token=agreement.token)

        if not accept_checkbox and not signature_data:
            messages.error(request, "اختر الموافقة بالمربع أو قم بالتوقيع.")
            return redirect("agreement_view", token=agreement.token)

        if accept_checkbox:
            agreement.accepted_checkbox = True
            agreement.accepted_at = timezone.now()
            agreement.status = "accepted"
            log_event(request, "agreement_accept", meta=f"token:{agreement.token}")

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
                log_event(request, "agreement_sign", meta=f"token:{agreement.token}")
            except Exception:
                messages.error(request, "تعذر حفظ التوقيع. جرّب مرة أخرى.")
                log_event(request, "security_block", meta="signature_save_failed")
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

    log_event(request, "view", meta=f"agreement_view:{agreement.token}")
    return render(request, "accounts/agreement.html", {"agreement": agreement})


# --------------------------------------------------
# Payment Page
# --------------------------------------------------
@login_required
@csrf_protect
def payment_page(request, token):
    agreement = get_object_or_404(UserAgreement, token=token)

    if agreement.user_id != request.user.id:
        return HttpResponseForbidden("غير مصرح لك بالوصول.")

    if agreement.status != "payment_pending":
        return redirect("payment_pending_review", token=agreement.token)

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
        client_receipt = (request.POST.get("client_payment_receipt", "") or "").strip()
        receipt_image = request.FILES.get("client_receipt_image")

        try:
            client_receipt = validate_receipt_code(client_receipt, "client_payment_receipt")
        except ValidationError as e:
            messages.error(request, str(e))
            log_event(request, "security_block", meta=f"payment_receipt_invalid:{str(e)}")
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

        log_event(request, "payment_submit", meta=f"token:{agreement.token} receipt:{client_receipt}")
        messages.success(request, "تم إرسال رقم الإيصال وصورته بنجاح. بانتظار موافقة المكتب.")
        return redirect("payment_pending_review", token=agreement.token)

    office_invoice_number = agreement.office_invoice_number or agreement.sadad_bill_number or "—"

    log_event(request, "view", meta=f"payment_page:{agreement.token}")

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

    log_event(request, "view", meta=f"payment_pending_review:{agreement.token}")

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

    log_event(request, "view", meta=f"payment_success:{agreement.token}")

    return render(request, "accounts/payment_success.html", {"agreement": agreement})


# ==================================================
# 🟦 Master Views
# ==================================================
@staff_member_required
def master_clients_list(request):
    q = (request.GET.get("q") or "").strip()

    folders_qs = ClientMasterFolder.objects.select_related("user").all().order_by("-created_at")
    if q:
        try:
            q_safe = validate_safe_text(q, "master_search", max_len=100, min_len=1)
        except ValidationError:
            q_safe = ""
        if q_safe:
            folders_qs = folders_qs.filter(
                Q(user__username__icontains=q_safe) |
                Q(user__email__icontains=q_safe) |
                Q(national_id__icontains=q_safe) |
                Q(user__phone_number__icontains=q_safe)
            )

    paginator = Paginator(folders_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    log_event(request, "view", meta="master_clients_list")

    return render(
        request,
        "accounts/master/clients_list.html",
        {"q": q, "page_obj": page_obj},
    )


@staff_member_required
def master_client_detail(request, folder_id):
    folder = get_object_or_404(
        ClientMasterFolder.objects.select_related("user"),
        id=folder_id
    )

    messages_qs = folder.messages.select_related("sender").all().order_by("-created_at")
    docs_qs = folder.documents.select_related("uploaded_by").all().order_by("-created_at")

    msg_paginator = Paginator(messages_qs, 15)
    msg_page = request.GET.get("mpage")
    msg_page_obj = msg_paginator.get_page(msg_page)

    folder.messages.filter(direction="client", is_read=False).update(is_read=True)

    profile = UserProfile.objects.filter(user=folder.user).first()

    log_event(request, "view", meta=f"master_client_detail:{folder.id}")

    return render(
        request,
        "accounts/master/client_detail.html",
        {
            "folder": folder,
            "profile": profile,
            "msg_page_obj": msg_page_obj,
            "docs": docs_qs,
            "cases": folder.user.account_cases.all().order_by("-created_at"),
            "agreements": folder.user.agreements.all().order_by("-created_at"),
        },
    )


@staff_member_required
@require_POST
@csrf_protect
def master_send_message(request, folder_id):
    folder = get_object_or_404(ClientMasterFolder, id=folder_id)

    body = (request.POST.get("message") or "").strip()
    try:
        body = validate_safe_multiline(body, "master_message", max_len=1500, min_len=1)
    except ValidationError as e:
        messages.error(request, str(e))
        log_event(request, "security_block", meta=f"master_message_invalid:{str(e)}")
        return redirect("master_client_detail", folder_id=folder.id)

    ClientMasterMessage.objects.create(
        folder=folder,
        sender=request.user,
        direction="lawyer",
        message=body,
        is_read=True,
    )

    try:
        last_case = folder.user.account_cases.order_by("-created_at").first()
        _save_sentiment(request.user, last_case, "lawyer", body)
    except Exception:
        pass

    log_event(request, "master_message", meta=f"folder:{folder.id}")
    messages.success(request, "تم إرسال الرسالة للعميل.")
    return redirect("master_client_detail", folder_id=folder.id)


@staff_member_required
def master_events_dashboard(request):
    q = (request.GET.get("q") or "").strip()
    et = (request.GET.get("type") or "").strip()

    qs = AuditEvent.objects.select_related("user").all().order_by("-created_at")

    if et:
        allowed = {c[0] for c in AuditEvent.EVENT_TYPES}
        if et in allowed:
            qs = qs.filter(event_type=et)

    if q:
        try:
            q_safe = validate_safe_text(q, "events_search", max_len=80, min_len=1)
        except ValidationError:
            q_safe = ""
        if q_safe:
            qs = qs.filter(
                Q(user__username__icontains=q_safe) |
                Q(path__icontains=q_safe) |
                Q(ip__icontains=q_safe)
            )

    paginator = Paginator(qs, 30)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    log_event(request, "view", meta="master_events_dashboard")

    return render(
        request,
        "accounts/master/events_dashboard.html",
        {
            "q": q,
            "type": et,
            "page_obj": page_obj,
            "types": AuditEvent.EVENT_TYPES,
        },
    )
