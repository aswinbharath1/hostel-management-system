from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from . models import User
# Register your models here.

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (
    ('Additional Information', {
    'fields': (
        'phone_number',
        'role',
        'full_name',
        'date_of_birth',
        'gender',
        'address',
        'emergency_contact_name',
        'emergency_contact_number',
        'category',
        'other_category',
        'category_details',
        )
    }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields':('email','phone_number' , 'role')
        }),

    )

    list_display = (
        'username',
        'email',
        'phone_number',
        'role',
        'is_active',
        'is_staff'
    )

    list_filter = ('role', 'is_active', 'is_staff')