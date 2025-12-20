from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User


class RegisterForm(UserCreationForm):

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'password1',
            'password2',
        ]

    def clean_username(self):
        username = self.cleaned_data['username']

        if ' ' in username:
            raise ValidationError("اسم المستخدم لا يجب أن يحتوي على مسافات")

        if len(username) < 4:
            raise ValidationError("اسم المستخدم يجب ألا يقل عن 4 أحرف")

        if User.objects.filter(username=username).exists():
            raise ValidationError("اسم المستخدم مستخدم بالفعل")

        return username

    def clean_email(self):
        email = self.cleaned_data['email']

        if User.objects.filter(email=email).exists():
            raise ValidationError("البريد الإلكتروني مستخدم بالفعل")

        return email

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number']

        if not phone.isdigit():
            raise ValidationError("رقم الجوال يجب أن يحتوي على أرقام فقط")

        if User.objects.filter(phone_number=phone).exists():
            raise ValidationError("رقم الجوال مستخدم بالفعل")

        return phone
