# accounts/security.py
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as dj_validate_email
from django.utils.html import escape


# --------------------------------------------------
# Notes:
# 1) Input Validation (Whitelisting): reject unknown/bad.
# 2) Sanitization: optional normalization, not a security boundary.
# 3) Output Encoding: ALWAYS encode on output (Django templates auto-escape by default).
# --------------------------------------------------


USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{4,30}$")
PHONE_RE = re.compile(r"^[0-9]{9,15}$")
RECEIPT_RE = re.compile(r"^[A-Za-z0-9\-]{4,64}$")
SAFE_TEXT_RE = re.compile(r"^[\s\u0600-\u06FFa-zA-Z0-9\.\,\:\;\-\_\(\)\[\]\!\?\@\#\/\\\n\r]+$")


def _clean(s: str) -> str:
    # Sanitization (non-security): trim + normalize newlines.
    if s is None:
        return ""
    s = str(s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()


def validate_username(value: str) -> str:
    value = _clean(value)
    if not value:
        raise ValidationError("يرجى إدخال اسم المستخدم.")
    if not USERNAME_RE.match(value):
        raise ValidationError("اسم المستخدم غير صالح. استخدم أحرف/أرقام/underscore فقط (4-30).")
    return value


def validate_phone(value: str) -> str:
    value = _clean(value)
    if not value:
        return ""
    # allow leading + then strip it
    if value.startswith("+"):
        value = value[1:]
    if not PHONE_RE.match(value):
        raise ValidationError("رقم الجوال غير صالح. أرقام فقط (9-15).")
    return value


def validate_email_safe(value: str) -> str:
    value = _clean(value)
    if not value:
        return ""
    try:
        dj_validate_email(value)
    except ValidationError:
        raise ValidationError("البريد الإلكتروني غير صالح.")
    if len(value) > 254:
        raise ValidationError("البريد الإلكتروني طويل جدًا.")
    return value


def validate_receipt_code(value: str, field_name: str = "receipt") -> str:
    value = _clean(value)
    if not value:
        raise ValidationError("رقم الإيصال مطلوب.")
    if not RECEIPT_RE.match(value):
        raise ValidationError("رقم الإيصال غير صالح. مسموح أحرف/أرقام/- فقط.")
    return value


def validate_choice(value: str, allowed: set, field_name: str = "choice") -> str:
    value = _clean(value)
    if value not in allowed:
        raise ValidationError(f"قيمة غير مسموحة في {field_name}.")
    return value


def validate_safe_text(value: str, field_name: str, max_len: int = 2000, min_len: int = 1) -> str:
    value = _clean(value)
    if min_len and len(value) < min_len:
        raise ValidationError(f"الحقل {field_name} قصير جدًا.")
    if max_len and len(value) > max_len:
        raise ValidationError(f"الحقل {field_name} طويل جدًا.")
    # Whitelisting for text fields: reject unexpected symbols/scripts.
    if value and not SAFE_TEXT_RE.match(value):
        raise ValidationError(f"الحقل {field_name} يحتوي رموز/نص غير مسموح.")
    return value


def output_encode(text: str) -> str:
    # Output Encoding (use if you ever output into HTML manually).
    return escape(text or "")
