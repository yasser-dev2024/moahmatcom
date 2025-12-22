# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("profile/", views.profile_update_view, name="profile_update"),
    path("case/create/", views.case_create, name="case_create"),

    path("suspended/", views.account_suspended, name="account_suspended"),

    path("agreement/<str:token>/", views.agreement_view, name="agreement_view"),

    # الدفع
    path("payment/<str:token>/", views.payment_page, name="payment_page"),
    path("payment/<str:token>/pending/", views.payment_pending_review, name="payment_pending_review"),

    # نجاح الدفع (بعد اعتماد المكتب)
    path("payment/<str:token>/success/", views.payment_success, name="payment_success"),
]
