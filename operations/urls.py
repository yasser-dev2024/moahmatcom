from django.urls import path
from .views import create_case

urlpatterns = [
    path('create/', create_case, name='create_case'),
]
