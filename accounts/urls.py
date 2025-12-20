from django.urls import path
from .views import (
    register_view,
    login_view,
    logout_view,
    user_dashboard,
    profile_update_view,
    case_create,          # View رفع قضية جديدة
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
]
