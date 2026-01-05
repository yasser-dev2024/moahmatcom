# operations/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Case

# ✅ نستخدم نفس طبقة الأمان من accounts (بدون تغيير هيكل التطبيق)
from accounts.security import validate_safe_text, validate_choice


@login_required
def create_case(request):
    if request.method == 'POST':
        try:
            case_type = (request.POST.get('case_type') or '').strip()
            title = validate_safe_text(request.POST.get('title', ''), 'ops_case_title', max_len=200, min_len=3)
            description = validate_safe_text(request.POST.get('description', ''), 'ops_case_description', max_len=3000, min_len=5)

            # case_type whitelist حسب موديل operations/models.py
            allowed_case_types = {'civil', 'commercial', 'family', 'criminal', 'other'}
            case_type = validate_choice(case_type, allowed_case_types, 'ops_case_type')

        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('create_case')

        Case.objects.create(
            user=request.user,
            case_type=case_type,
            title=title,
            description=description,
            attachment=request.FILES.get('attachment'),
        )

        messages.success(request, 'تم رفع القضية بنجاح')
        return redirect('user_dashboard')

    return render(request, 'operations/create_case.html')
