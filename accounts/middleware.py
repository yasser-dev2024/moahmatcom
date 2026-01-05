# accounts/middleware.py
import time
import hashlib
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


def _ip_from_request(request) -> str:
    # لا تثق بالـ X-Forwarded-For إلا إذا كنت خلف Proxy مضبوط. في بيئتك المحلية خله بسيط.
    ip = request.META.get("REMOTE_ADDR", "") or ""
    return ip.strip()[:64]


def _cache_key(prefix: str, parts: list[str]) -> str:
    raw = prefix + ":" + "|".join([p or "" for p in parts])
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"{prefix}:{h}"


class RateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting بسيط (Server-Side) ضد الهجمات الآلية.
    - يطبق على POST بشكل افتراضي.
    - لا يغير تصميم الموقع.
    """

    # requests per window
    WINDOW_SECONDS = 60
    MAX_POSTS_PER_WINDOW = 60  # عدّلها لاحقًا حسب احتياجك

    def process_request(self, request):
        if request.method != "POST":
            return None

        ip = _ip_from_request(request)
        path = (request.path or "")[:200]

        key = _cache_key("rl_post", [ip, path])
        now = int(time.time())

        data = cache.get(key) or {"ts": now, "count": 0}
        # reset if window expired
        if now - int(data.get("ts", now)) > self.WINDOW_SECONDS:
            data = {"ts": now, "count": 0}

        data["count"] = int(data.get("count", 0)) + 1
        cache.set(key, data, timeout=self.WINDOW_SECONDS + 5)

        if data["count"] > self.MAX_POSTS_PER_WINDOW:
            return HttpResponseForbidden("تم حظر الطلب مؤقتًا بسبب عدد محاولات مرتفع.")
        return None


class LoginLockoutMiddleware(MiddlewareMixin):
    """
    قفل مؤقت بعد محاولات فاشلة (منع brute force)
    - يتم الاعتماد عليه من داخل login_view (نفس المفهوم: السيرفر هو الحكم النهائي).
    """

    LOCK_WINDOW = 15 * 60
    MAX_FAILS = 6

    @staticmethod
    def is_locked(ip: str, username: str) -> bool:
        key = _cache_key("login_lock", [ip, username])
        fails = int(cache.get(key) or 0)
        return fails >= LoginLockoutMiddleware.MAX_FAILS

    @staticmethod
    def register_fail(ip: str, username: str) -> None:
        key = _cache_key("login_lock", [ip, username])
        fails = int(cache.get(key) or 0) + 1
        cache.set(key, fails, timeout=LoginLockoutMiddleware.LOCK_WINDOW)

    @staticmethod
    def clear(ip: str, username: str) -> None:
        key = _cache_key("login_lock", [ip, username])
        cache.delete(key)
