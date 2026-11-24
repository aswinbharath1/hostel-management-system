from django.utils.dateparse import parse_date
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model , login, authenticate , logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
import re
from datetime import date
from .models import ResidentCategory, ResidentCategoryField


# Create your views here.

User = get_user_model()


def get_auth_context(initial_panel='', form_data=None):
    categories = list(
        ResidentCategory.objects
        .filter(is_active=True)
        .prefetch_related('custom_fields')
    )

    category_fields_data = {}

    for category in categories:
        category_fields_data[str(category.id)] = [
            {
                'key': field.field_key,
                'label': field.label,
                'type': field.field_type.lower(),
            }
            for field in category.custom_fields.all()
            if field.is_active
        ]

    return {
        'form_data': form_data or {},
        'initial_panel': initial_panel,
        'categories': categories,
        'category_fields_data': category_fields_data,
    }



@never_cache
def auth_view(request):
    initial_panel = request.session.pop('auth_panel', '')

    return render(
        request,
        'accounts/auth.html',
        get_auth_context(initial_panel)
    )


def register_view(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth') or None
        gender = request.POST.get('gender', '')
        category_id = request.POST.get('category', '')

        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not all([
            full_name, email, phone_number,
            category_id, password1, password2
        ]):
            messages.error(
                request,
                'Please fill in all required fields.'
            )

        elif gender not in User.Gender.values:
            messages.error(request, 'Please select a valid gender.')

        elif User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')

        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')

        else:
            category = ResidentCategory.objects.filter(
                id=category_id,
                is_active=True
            ).first()

            if not category:
                messages.error(
                    request,
                    'Please select a valid active category.'
                )
            else:
                try:
                    validate_password(password1)

                    category_details = {}

                    # Get active fields configured by Admin
                    fields = category.custom_fields.filter(
                        is_active=True
                    )

                    # Save only the values provided by the resident
                    for field in fields:
                        value = request.POST.get(
                            field.field_key, ''
                        ).strip()

                        if value:
                            category_details[field.field_key] = value

                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=password1,
                        full_name=full_name,
                        phone_number=phone_number,
                        date_of_birth=date_of_birth,
                        gender=gender,
                        category=category,
                        category_details=category_details,
                        profile_completed=False
                    )


                    login(request, user)

                    messages.success(
                        request,
                        'Registration successful! Please complete your profile.'
                    )

                    return redirect('complete_profile')

                except ValidationError as error:
                    messages.error(
                        request,
                        ' '.join(error.messages)
                    )

        return render(
            request,
            'accounts/auth.html',
            get_auth_context('signup', request.POST.dict())
        )

    return redirect('auth')

# Login Users
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        user = User.objects.filter(email=email).first()

        if user:
            authenticated_user = authenticate(
                request,
                username=user.username,
                password=password
            )

            if authenticated_user is not None:
                login(request, authenticated_user)

                if authenticated_user.role == User.Role.ADMIN:
                    return redirect('/admin/')

                elif authenticated_user.role == User.Role.WARDEN:
                    return redirect('warden_dashboard')

                else:
                    if not authenticated_user.profile_completed:
                        return redirect('complete_profile')

                    return redirect('resident_dashboard')

        messages.error(
            request,
            'Invalid UserName or Password !! Check Your Credentials Again'
        )

    return render(request, 'accounts/auth.html', {
        'form_data': {},
        'initial_panel': 'signin'
    })

#Logout Users

@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request,'You have been Logged Out Successfully. ')
    return redirect('auth')


#complete profile for the google authenticated users 

@login_required
def complete_profile(request):
    user = request.user

    if user.profile_completed:
        return redirect('resident_dashboard')

    categories = ResidentCategory.objects.filter(is_active=True)

    # Prepare dynamic fields for each category.
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

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '')
        gender = request.POST.get('gender', '')
        address = request.POST.get('address', '').strip()

        emergency_contact_name = request.POST.get(
            'emergency_contact_name', ''
        ).strip()

        emergency_contact_number = request.POST.get(
            'emergency_contact_number', ''
        ).strip()

        category_id = request.POST.get('category', '')

        errors = []

        if not all([
            full_name, phone_number, date_of_birth, gender,
            address, emergency_contact_name,
            emergency_contact_number, category_id
        ]):
            errors.append('Please fill in all required fields.')

        dob = parse_date(date_of_birth)

        if date_of_birth and not dob:
            errors.append('Please enter a valid date of birth.')
        elif dob and dob > date.today():
            errors.append('Date of birth cannot be in the future.')

        if gender not in User.Gender.values:
            errors.append('Please select a valid gender.')

        category = categories.filter(id=category_id).first()

        if not category:
            errors.append('Please select a valid resident category.')

        if not errors:
            category_details = {}

            # Read active fields configured by Admin.
            for field in category.custom_fields.filter(is_active=True):
                value = request.POST.get(field.field_key, '').strip()

                if value:
                    category_details[field.field_key] = value

            user.full_name = full_name
            user.phone_number = phone_number
            user.date_of_birth = dob
            user.gender = gender
            user.address = address
            user.emergency_contact_name = emergency_contact_name
            user.emergency_contact_number = emergency_contact_number
            user.category = category
            user.category_details = category_details
            user.profile_completed = True

            user.save()

            messages.success(
                request,
                'Your profile has been completed successfully!'
            )
            return redirect('resident_dashboard')

        for error in errors:
            messages.error(request, error)

    return render(request, 'accounts/complete_profile.html', {
        'user': user,
        'category_choices': categories,
        'gender_choices': User.Gender.choices,
        'category_fields_data': category_fields_data,
    })


@login_required
def edit_profile(request):
    user = request.user

    categories = list(
        ResidentCategory.objects.filter(is_active=True)
    )

    # Keep the resident's existing category available if Admin deactivated it.
    if user.category and not user.category.is_active:
        if user.category not in categories:
            categories.append(user.category)

    # Prepare category-specific fields from the database.
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

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '')
        gender = request.POST.get('gender', '')
        address = request.POST.get('address', '').strip()

        emergency_contact_name = request.POST.get(
            'emergency_contact_name', ''
        ).strip()

        emergency_contact_number = request.POST.get(
            'emergency_contact_number', ''
        ).strip()

        category_id = request.POST.get('category', '')

        errors = []

        if not full_name:
            errors.append('Full name is required.')

        if not re.fullmatch(r'[0-9]{10}', phone_number):
            errors.append('Phone number must contain exactly 10 digits.')

        if not re.fullmatch(r'[0-9]{10}', emergency_contact_number):
            errors.append(
                'Emergency contact number must contain exactly 10 digits.'
            )

        dob = parse_date(date_of_birth)

        if not dob:
            errors.append('Please enter a valid date of birth.')
        elif dob > date.today():
            errors.append('Date of birth cannot be in the future.')

        if gender not in User.Gender.values:
            errors.append('Please select a valid gender.')

        if not address:
            errors.append('Address is required.')

        if not emergency_contact_name:
            errors.append('Emergency contact name is required.')

        category = next(
            (item for item in categories if str(item.id) == category_id),
            None
        )

        if not category:
            errors.append('Please select a valid resident category.')

        if not errors:
            category_details = {}

            # Only accept fields configured for the selected category.
            for field in category.custom_fields.filter(is_active=True):
                value = request.POST.get(field.field_key, '').strip()

                if value:
                    category_details[field.field_key] = value

            user.full_name = full_name
            user.phone_number = phone_number
            user.date_of_birth = dob
            user.gender = gender
            user.address = address
            user.emergency_contact_name = emergency_contact_name
            user.emergency_contact_number = emergency_contact_number
            user.category = category
            user.category_details = category_details

            user.save()

            messages.success(
                request,
                'Your profile has been updated successfully!'
            )
            return redirect('resident_profile')

        for error in errors:
            messages.error(request, error)

    return render(request, 'residents/profile.html', {
        'user': user,
        'categories': categories,
        'gender_choices': User.Gender.choices,
        'category_fields_data': category_fields_data,
        'is_edit': True,
    })