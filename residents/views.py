from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.models import ResidentCategory
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.core.exceptions import ValidationError

from properties.models import Room
from reservations.models import AccommodationRequest

User = get_user_model()


@login_required
def resident_dashboard(request):
    if not request.user.profile_completed:
        return redirect('complete_profile')

    return render(request, 'residents/dashboard.html')


@login_required
def resident_profile(request):
    if not request.user.profile_completed:
        return redirect('complete_profile')

    categories = list(
        ResidentCategory.objects.filter(is_active=True)
    )

    # Include the resident's existing category if inactive.
    if request.user.category and not request.user.category.is_active:
        if request.user.category not in categories:
            categories.append(request.user.category)

    category_fields_data = {}

    for category in categories:
        category_fields_data[str(category.id)] = [
            {
                'key': field.field_key,
                'label': field.label,
                'type': field.field_type.lower(),
            }
            for field in category.custom_fields.filter(is_active=True)
        ]

    return render(request, 'residents/profile.html', {
        'categories': categories,
        'gender_choices': User.Gender.choices,
        'category_fields_data': category_fields_data,
    })


@login_required
def accommodation_request(request):

    if request.user.role != User.Role.RESIDENT:
        return redirect('auth')

    if not request.user.profile_completed:
        return redirect('complete_profile')

    if request.method == 'POST':

        room_type = request.POST.get('preferred_room_type')
        check_in = parse_date(request.POST.get('requested_check_in', ''))
        check_out = parse_date(request.POST.get('expected_check_out', ''))
        notes = request.POST.get('additional_notes', '').strip()

        valid_room_types = dict(Room.RoomType.choices)

        if room_type not in valid_room_types:
            messages.error(request, 'Please select a valid room type.')

        elif not check_in or not check_out:
            messages.error(request, 'Please enter valid dates.')

        elif check_in < timezone.localdate():
            messages.error(request, 'Check-in date cannot be in the past.')

        elif check_out <= check_in:
            messages.error(
                request,
                'Expected check-out must be after check-in.'
            )

        else:
            accommodation = AccommodationRequest(
                resident=request.user,
                preferred_room_type=room_type,
                requested_check_in=check_in,
                expected_check_out=check_out,
                additional_notes=notes,
            )

            try:
                accommodation.full_clean()
                accommodation.save()

                messages.success(
                    request,
                    'Your accommodation request has been submitted successfully.'
                )
                return redirect('resident_accommodation_request')

            except ValidationError as error:
                for field_errors in error.message_dict.values():
                    for error_message in field_errors:
                        messages.error(request, error_message)

    requests = AccommodationRequest.objects.filter(
        resident=request.user
    ).order_by('-created_at')

    context = {
        'requests': requests,
        'room_type_choices': Room.RoomType.choices,
        'today': timezone.localdate(),
    }

    return render(
        request,
        'residents/accommodation_request.html',
        context
    )
