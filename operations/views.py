from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Case


@login_required
def create_case(request):
    if request.method == 'POST':
        Case.objects.create(
            user=request.user,
            case_type=request.POST.get('case_type'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            attachment=request.FILES.get('attachment'),
        )

        messages.success(request, 'تم رفع القضية بنجاح')
        return redirect('user_dashboard')

    return render(request, 'operations/create_case.html')
