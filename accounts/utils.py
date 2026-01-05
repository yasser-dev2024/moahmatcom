import re
from typing import Tuple


ARABIC_LETTERS_RE = re.compile(r"^[\u0600-\u06FF\s]+$")


def safe_strip(value: str, max_len: int = 5000) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    return value[:max_len]


def whitelist_username(username: str) -> bool:
    """
    Whitelisting:
    - أحرف/أرقام/underscore فقط
    - 4 إلى 30
    - بدون مسافات
    """
    if not username:
        return False
    username = username.strip()
    if " " in username:
        return False
    if not (4 <= len(username) <= 30):
        return False
    return bool(re.match(r"^[A-Za-z0-9_]+$", username))


def whitelist_phone(phone: str) -> bool:
    """
    Whitelisting للجوال:
    - أرقام فقط
    - طول معقول (8-15)
    """
    if not phone:
        return False
    phone = phone.strip()
    if not phone.isdigit():
        return False
    return 8 <= len(phone) <= 15


def simple_arabic_sentiment(text: str) -> Tuple[str, int]:
    """
    تحليل مشاعر عربي بسيط Rule-based (بدون أي API خارجي).
    يرجع: (label, score)
    score: موجب/سالب/صفر
    """
    t = safe_strip(text, 8000)
    t_low = t.lower()

    positive_words = [
        "ممتاز", "رائع", "الحمد", "شكرا", "شكرًا", "مبروك", "جميل", "مرتاح", "اطمئن", "اطمئنان",
        "نجاح", "فزت", "فوز", "سعيد", "سعادة", "سرور", "أفضل"
    ]
    negative_words = [
        "قلق", "خوف", "مشكلة", "مزعج", "سيء", "تعب", "ضغط", "مضغوط", "متوتر", "حزين", "حزن",
        "خسارة", "استئناف", "رفض", "مرفوض", "غضب", "غاضب", "سيئ"
    ]

    score = 0
    for w in positive_words:
        if w.lower() in t_low:
            score += 1
    for w in negative_words:
        if w.lower() in t_low:
            score -= 1

    if score > 0:
        return ("positive", score)
    if score < 0:
        return ("negative", score)
    return ("neutral", 0)
