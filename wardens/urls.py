from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('residents/', views.resident_list, name='warden_resident_list'),
    path('residents/<int:resident_id>/',views.resident_detail,name='warden_resident_detail'),
    path('allocations/',views.allocation_list,name='warden_allocation_list'),
]