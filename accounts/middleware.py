# accounts/middleware.py
import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.http import HttpResponseForbidden

logger = logging.getLogger("security")


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Headers أساسية تقلل OWASP Top 10 (XSS/Clickjacking/MIME sniffing...)
    بدون مكتبات خارجية.
    """

    def process_response(self, request, response):
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # CSP خفيف (ممكن تشديده لاحقًا حسب مواردك)
        # انت تستخدم Tailwind CDN + Google Fonts
        csp = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https:; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; "
            "font-src 'self' https://fonts.gstatic.com data:; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
        )
        response["Content-Security-Policy"] = csp

        return response


class SimpleRateLimitMiddleware(MiddlewareMixin):
    """
    Rate limiting بسيط على مسارات حساسة لتقليل brute-force.
    """

    WINDOW_SECONDS = 60
    LIMIT = 20  # 20 طلب بالدقيقة

    SENSITIVE_PREFIXES = (
        "/accounts/login/",
        "/accounts/register/",
    )

    def process_request(self, request):
        path = request.path or ""
        if not any(path.startswith(p) for p in self.SENSITIVE_PREFIXES):
            return None

        ip = self._get_ip(request)
        key = f"rl:{ip}:{path}"
        now = int(time.time())

        bucket = cache.get(key)
        if not bucket:
            bucket = {"start": now, "count": 0}

        # reset window
        if now - bucket["start"] >= self.WINDOW_SECONDS:
            bucket = {"start": now, "count": 0}

        bucket["count"] += 1
        cache.set(key, bucket, timeout=self.WINDOW_SECONDS)

        if bucket["count"] > self.LIMIT:
            logger.warning("Rate limit exceeded", extra={"ip": ip, "path": path})
            return HttpResponseForbidden("تم حظر الطلب مؤقتًا بسبب كثرة المحاولات.")

        return None

    @staticmethod
    def _get_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
