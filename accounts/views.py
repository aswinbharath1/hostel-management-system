
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()
# Create your views here.
def auth_view(request):
    return render(request, 'accounts/auth.html')

