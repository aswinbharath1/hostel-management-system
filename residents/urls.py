from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.resident_dashboard, name='resident_dashboard'),
    path('profile/', views.resident_profile, name='resident_profile'),

]