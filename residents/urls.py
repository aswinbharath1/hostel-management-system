from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.resident_dashboard, name='resident_dashboard'),
    path('profile/', views.resident_profile, name='resident_profile'),
    path(    'accommodation-request/',    views.accommodation_request,    name='resident_accommodation_request'),
    path(    'rent-payments/',    views.resident_rent_payments,    name='resident_rent_payments'),
]