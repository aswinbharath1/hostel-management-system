
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, ResidentCategory,ResidentCategoryField


class ResidentCategoryFieldInline(admin.TabularInline):
    model = ResidentCategoryField
    extra = 1
    prepopulated_fields = {
        'field_key': ('label',)
    }

@admin.register(ResidentCategory)
class ResidentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ResidentCategoryFieldInline]




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
                'category_details',
                'profile_completed',
            )
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {
            'fields': ('email', 'phone_number', 'role')
        }),
    )

    list_display = (
        'username',
        'email',
        'phone_number',
        'role',
        'category',
        'is_active',
        'is_staff',
    )

    list_filter = ('role', 'category', 'is_active', 'is_staff')
