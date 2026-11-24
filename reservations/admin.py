from django.contrib import admin
from .models import AccommodationRequest, Reservation

# Register your models here.



@admin.register(AccommodationRequest)
class AccommodationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'resident',
        'preferred_room_type',
        'requested_check_in',
        'expected_check_out',
        'status',
        'created_at',
    )

    list_filter = ('status', 'preferred_room_type')
    search_fields = ('resident__full_name', 'resident__email')
    readonly_fields = ('created_at', 'updated_at', 'reviewed_at')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        'resident',
        'preferred_room_type',
        'check_in_date',
        'expected_check_out',
        'status',
        'created_by',
    )

    list_filter = ('status', 'preferred_room_type')
    search_fields = ('resident__full_name', 'resident__email')
    readonly_fields = ('created_at', 'updated_at')
