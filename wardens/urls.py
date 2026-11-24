from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.warden_dashboard, name='warden_dashboard'),
    path('residents/', views.resident_list, name='warden_resident_list'),
    path('residents/<int:resident_id>/',views.resident_detail,name='warden_resident_detail'),
    path('allocations/',views.allocation_list,name='warden_allocation_list'),
    path('allocations/allocate/',views.allocate_bed,name='warden_allocate_bed'),
    path('allocations/<int:allocation_id>/vacate/',views.vacate_bed,name='warden_vacate_bed'),
    path('rooms/', views.room_list, name='warden_room_list'),
    path('rooms/<int:room_id>/',views.room_detail,name='warden_room_detail'),
    path(    'accommodation-requests/',    views.accommodation_request_list,    name='warden_accommodation_requests'),
    path(    'accommodation-requests/<int:request_id>/',views.accommodation_request_detail,name='warden_accommodation_request_detail'),
    path('accommodation-requests/<int:request_id>/review/',views.review_accommodation_request,name='warden_review_accommodation_request'),
    




]