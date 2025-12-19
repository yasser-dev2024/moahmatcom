from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import register_view, login_view

urlpatterns = [
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),

    # تسجيل الخروج
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
]
