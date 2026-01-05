# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ----------------------------------
    # Auth
    # ----------------------------------
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ----------------------------------
    # User Area
    # ----------------------------------
    path("dashboard/", views.user_dashboard, name="user_dashboard"),
    path("profile/", views.profile_update_view, name="profile_update"),
    path("case/create/", views.case_create, name="case_create"),

    # ----------------------------------
    # Account Status
    # ----------------------------------
    path("suspended/", views.account_suspended, name="account_suspended"),

    # ----------------------------------
    # Agreements
    # ----------------------------------
    path("agreement/<str:token>/", views.agreement_view, name="agreement_view"),

    # ----------------------------------
    # Payments
    # ----------------------------------
    path("payment/<str:token>/", views.payment_page, name="payment_page"),
    path("payment/<str:token>/pending/", views.payment_pending_review, name="payment_pending_review"),
    path("payment/<str:token>/success/", views.payment_success, name="payment_success"),

    # ==================================================
    # 🟦 Master (Lawyer / Admin Dashboard)
    # ==================================================
    path("master/clients/", views.master_clients_list, name="master_clients_list"),
    path("master/clients/<int:folder_id>/", views.master_client_detail, name="master_client_detail"),
    path("master/clients/<int:folder_id>/send-message/", views.master_send_message, name="master_send_message"),

    # ✅ Events dashboard
    path("master/events/", views.master_events_dashboard, name="master_events_dashboard"),
]
