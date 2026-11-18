
from django.contrib import admin
from django import forms
from django.db import transaction
from .models import Building, Floor, Room, Bed, Facility


class RoomAdminForm(forms.ModelForm):

    bed_rent = forms.DecimalField(
        label="Monthly Rent (Per Bed)",
        max_digits=10,
        decimal_places=2,
        min_value=0,
        help_text="This rent will be applied to every bed in this room."
    )

    class Meta:
        model = Room
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            first_bed = self.instance.beds.first()

            if first_bed:
                self.fields['bed_rent'].initial = first_bed.monthly_rent
            else:
                self.fields['bed_rent'].initial = 0

    def clean_capacity(self):
        capacity = self.cleaned_data['capacity']

        if capacity < 1:
            raise forms.ValidationError(
                "Room capacity must be at least 1."
            )

        if self.instance.pk:
            occupied_count = self.instance.beds.filter(
                allocations__is_active=True
            ).count()

            if capacity < occupied_count:
                raise forms.ValidationError(
                    f"This room has {occupied_count} occupied bed(s). "
                    "Capacity cannot be reduced below this number."
                )

        return capacity


class BedInline(admin.TabularInline):
    model = Bed
    extra = 0
    readonly_fields = ('bed_number', 'monthly_rent')
    can_delete = False
    fields = ('bed_number', 'monthly_rent')

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    form = RoomAdminForm

    list_display = ('room_number', 'floor', 'room_type', 'capacity')
    list_filter = ('room_type', 'floor')
    filter_horizontal = ('facilities',)
    inlines = [BedInline]

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)

            rent = form.cleaned_data['bed_rent']

            existing_beds = list(obj.beds.order_by('id'))

            # Remove available beds first when capacity is reduced
            if len(existing_beds) > obj.capacity:

                beds_to_remove = len(existing_beds) - obj.capacity

                available_beds = [
                    bed for bed in existing_beds
                    if not bed.allocations.filter(is_active=True).exists()
                ]

                for bed in available_beds[:beds_to_remove]:
                    bed.delete()

            # Create missing beds when capacity is increased
            elif len(existing_beds) < obj.capacity:
                existing_numbers = set(
                    obj.beds.values_list('bed_number', flat=True)
                )

                number = 1

                while obj.beds.count() < obj.capacity:
                    bed_number = f"Bed {number}"

                    if bed_number not in existing_numbers:
                        Bed.objects.create(
                            room=obj,
                            bed_number=bed_number,
                            monthly_rent=rent
                        )

                        existing_numbers.add(bed_number)

                    number += 1

            # Apply the same rent to every bed
            obj.beds.update(monthly_rent=rent)


admin.site.register(Building)
admin.site.register(Floor)


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ('bed_number', 'room', 'monthly_rent')
    readonly_fields = ('room', 'bed_number', 'monthly_rent')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
