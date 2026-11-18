from django.contrib import admin
from django import forms
from .models import Allocation
from accounts.models import User
from properties.models import Bed
from django.db import models
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

# Register your models here.



class AllocationAdminForm(forms.ModelForm):

    class Meta:
        model = Allocation
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show only resident accounts
        self.fields['resident'].queryset = User.objects.filter(
            role=User.Role.RESIDENT
        )

        # Show only beds that are not currently occupied
        available_beds = Bed.objects.exclude(
            allocations__is_active=True
        )

        # When editing, include the currently assigned bed
        if self.instance.pk and self.instance.is_active:
            available_beds = Bed.objects.filter(
                models.Q(allocations__is_active=False) |
                models.Q(allocations__isnull=True) |
                models.Q(pk=self.instance.bed_id)
            ).distinct()

        self.fields['bed'].queryset = available_beds


@admin.register(Allocation)
class AllocationAdmin(admin.ModelAdmin):
    form = AllocationAdminForm

    list_display = (
        'resident',
        'bed',
        'allocated_on',
        'vacated_on',
        'is_active'
    )

    list_filter = ('is_active', 'allocated_on')
    search_fields = (
        'resident__username',
        'resident__full_name',
        'bed__bed_number',
        'bed__room__room_number'
    )

    readonly_fields = ('allocated_on',)

    def save_model(self, request, obj, form, change):
        try:
            with transaction.atomic():
                obj.full_clean()
                super().save_model(request, obj, form, change)

        except IntegrityError:
            raise ValidationError(
                "This resident or bed already has an active allocation."
            )


    actions = ['vacate_allocations']
    @admin.action(description="Vacate selected allocations")
    def vacate_allocations(self, request, queryset):
        from django.utils import timezone

        active_allocations = queryset.filter(is_active=True)
        count = active_allocations.count()

        active_allocations.update(
            is_active=False,
            vacated_on=timezone.localdate()
        )

        self.message_user(
            request,
            f"{count} allocation(s) vacated successfully."
        )