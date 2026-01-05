# accounts/security.py
import re
from django.core.exceptions import ValidationError
from django.core.validators import validate_email as django_validate_email


# ================================
# Regex Whitelisting
# ================================
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{4,30}$")
_PHONE_RE = re.compile(r"^[0-9]{9,15}$")
_RECEIPT_RE = re.compile(r"^[A-Za-z0-9\-]{3,64}$")

# نص آمن عام: عربي/إنجليزي/أرقام/مسافات وبعض العلامات البسيطة (بدون < > { } ; ` إلخ)
# يسمح بـ . , - _ : / ( ) ؟ ! " ' + @ #
_SAFE_TEXT_RE = re.compile(r"^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FFA-Za-z0-9\s\.\,\-\_\:\(\)\/\?\!\u061F\"\'\+\@\#]{1,}$")


def _strip(v: str) -> str:
    return (v or "").strip()


def validate_username(value: str) -> str:
    v = _strip(value)
    if not v:
        return ""
    if not _USERNAME_RE.match(v):
        raise ValidationError("اسم المستخدم غير صالح. استخدم حروف/أرقام/underscore فقط (4-30).")
    return v


def validate_phone(value: str) -> str:
    v = _strip(value)
    if not v:
        return ""
    # تحويل عربي-هندي إلى أرقام إنجليزية إن وجدت (بشكل بسيط)
    trans = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    v = v.translate(trans)
    if not _PHONE_RE.match(v):
        raise ValidationError("رقم الجوال غير صالح. اكتب أرقام فقط (9-15).")
    return v


def validate_email_safe(value: str) -> str:
    v = _strip(value)
    if not v:
        return ""
    django_validate_email(v)
    if len(v) > 254:
        raise ValidationError("البريد الإلكتروني طويل جدًا.")
    return v


def validate_choice(value: str, allowed: set[str], field_name: str = "choice") -> str:
    v = _strip(value)
    if v not in allowed:
        raise ValidationError(f"قيمة غير صالحة في {field_name}.")
    return v


def validate_receipt_code(value: str, field_name: str = "receipt") -> str:
    v = _strip(value)
    if not v:
        raise ValidationError("رقم الإيصال مطلوب.")
    if not _RECEIPT_RE.match(v):
        raise ValidationError("رقم الإيصال غير صالح. استخدم أحرف/أرقام/شرطة فقط.")
    return v


def validate_safe_text(value: str, field_name: str, *, max_len: int = 500, min_len: int = 1) -> str:
    v = _strip(value)
    if not v:
        if min_len <= 0:
            return ""
        raise ValidationError(f"{field_name} مطلوب.")
    if len(v) < min_len:
        raise ValidationError(f"{field_name} قصير جدًا.")
    if len(v) > max_len:
        raise ValidationError(f"{field_name} طويل جدًا.")
    # رفض واضح لأخطر الرموز/الأنماط
    dangerous = ["<", ">", "{", "}", "`", ";", "/*", "*/", "<?", "?>", "javascript:", "onerror", "onload"]
    low = v.lower()
    if any(d in low for d in dangerous):
        raise ValidationError(f"{field_name}: محتوى غير مسموح.")
    if not _SAFE_TEXT_RE.match(v):
        raise ValidationError(f"{field_name}: يحتوي رموز غير مسموحة.")
    return v


def validate_safe_multiline(value: str, field_name: str, *, max_len: int = 3000, min_len: int = 1) -> str:
    """
    نص متعدد الأسطر: نفس whitelist لكن يسمح بالأسطر الجديدة.
    """
    v = (value or "").strip()
    if not v:
        if min_len <= 0:
            return ""
        raise ValidationError(f"{field_name} مطلوب.")
    if len(v) < min_len:
        raise ValidationError(f"{field_name} قصير جدًا.")
    if len(v) > max_len:
        raise ValidationError(f"{field_name} طويل جدًا.")

    # نفس رفض الأنماط الخطرة
    dangerous = ["<", ">", "{", "}", "`", ";", "/*", "*/", "<?", "?>", "javascript:", "onerror", "onload"]
    low = v.lower()
    if any(d in low for d in dangerous):
        raise ValidationError(f"{field_name}: محتوى غير مسموح.")

    # تحقق كل سطر على حدة
    for line in v.splitlines():
        line = line.strip()
        if not line:
            continue
        if not _SAFE_TEXT_RE.match(line):
            raise ValidationError(f"{field_name}: يحتوي رموز غير مسموحة.")
    return v
