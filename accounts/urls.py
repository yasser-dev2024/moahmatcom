from django.urls import path
from .views import (
    register_view,
    login_view,
    logout_view,
    user_dashboard,
    profile_update_view,
    case_create,

    # -----------------------------
    # Agreement / Suspension / Payment
    # -----------------------------
    account_suspended,
    agreement_view,
    payment_page,
)

urlpatterns = [

    # --------------------------------------------------
    # Authentication
    # --------------------------------------------------
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # --------------------------------------------------
    # User Dashboard & Profile
    # --------------------------------------------------
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('profile/', profile_update_view, name='profile_update'),

    # --------------------------------------------------
    # Cases
    # --------------------------------------------------
    path('cases/create/', case_create, name='case_create'),

    # --------------------------------------------------
    # Account Agreement Flow (NEW)
    # --------------------------------------------------
    path('suspended/', account_suspended, name='account_suspended'),
    path('agreement/<str:token>/', agreement_view, name='agreement_view'),
    path('payment/<str:token>/', payment_page, name='payment_page'),
]
