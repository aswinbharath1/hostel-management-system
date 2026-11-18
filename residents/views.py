from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required 
from accounts.models import User
from django.contrib.auth import get_user_model
# Create your views here.

@login_required
def resident_dashboard(request):
    if not request.user.profile_completed:
        return redirect('complete_profile')
    return render (request , 'residents/dashboard.html')

@login_required
def resident_profile(request):
    if not request.user.profile_completed:
        return redirect('complete_profile')
    User = get_user_model()

    return render(request, 'residents/profile.html', {
        'category_choices': User.Category.choices,
        'gender_choices': User.Gender.choices,
    })

