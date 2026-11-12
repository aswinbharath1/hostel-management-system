from django.shortcuts import render , redirect
from django.contrib.auth.decorators import login_required 

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

    return render(request, 'residents/profile.html')

