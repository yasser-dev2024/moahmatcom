from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("accounts.urls")),
    path("", include("legal.urls")),
    path("", include("operations.urls")),

    # 🔴 هذا السطر إلزامي
    path(
        "client/send-message/",
        accounts_views.client_send_message,
        name="client_send_message",
    ),
]
