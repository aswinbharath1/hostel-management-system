from django.utils.dateparse import parse_date
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model , login, authenticate , logout
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST


User = get_user_model()
# Create your views here.
@never_cache
def auth_view(request):
    initial_panel = request.session.pop('auth_panel', '')

    return render(request, 'accounts/auth.html', {
        'form_data': {},
        'initial_panel': initial_panel
    })

def register_view(request):
    if request.method =='POST':
        full_name = request.POST.get('full_name','').strip()
        email = request.POST.get('email','').lower()
        phone_number = request.POST.get('phone_number','').strip()
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender','')

        category = request.POST.get('category','')

        password1= request.POST.get('password1','').strip()
        password2= request.POST.get('password2','').strip()


        category_fields = {
            'STUDENT': [
                'institution_name', 'course', 'study_year'
            ],
            'JOB_SEEKER': [
                'qualification', 'preferred_job_location'
            ],
            'WORKING_PROFESSIONAL': [
                'company_name', 'designation', 'work_location'
            ],
            'EXAM_ASPIRANT': [
                'exam_name', 'coaching_institute'
            ],
            'INTERN': [
                'organisation', 'training_details'
            ],
            'BUSINESS': [
                'business_name', 'business_type'
            ],
            'MEDICAL': [
                'hospital_name', 'visit_purpose'
            ],
            'TEMPORARY': [
                'stay_purpose', 'stay_duration'
            ],
            
        }

        if not all([full_name, email, phone_number, category, password1, password2]):
            messages.error(request, 'Please fill in all required fields.')

        elif category not in User.Category.values:
            messages.error(request, 'Invalid resident category.')

        elif User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered.')

        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')

        else:
            try:
                # Validate password using Django's password validators
                validate_password(password1)

                # Collect category-specific information
                category_details = {}

                for field in category_fields.get(category, []):
                    value = request.POST.get(field, '').strip()

                    if value:
                        category_details[field] = value
                # Create resident account
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password1,
                    full_name=full_name,
                    phone_number=phone_number,
                    date_of_birth=date_of_birth,
                    gender= gender,
                    category=category,
                    category_details=category_details,
                    profile_completed=True
                )

                
                messages.success(
                request,
                'Registration successful! You can now sign in.'
                    )

                request.session['auth_panel'] = 'signin'

                return redirect('auth')

            except ValidationError as error:
                messages.error(request, ' '.join(error.messages))
        
        # Keep submitted data when registration fails
        return render(request, 'accounts/auth.html', {
            'form_data': request.POST.dict(),
            'initial_panel': 'signup'
        })
    return redirect('auth')



#login Users
def login_view(request):
    if request.method=='POST':
        email= request.POST.get('email','').strip().lower()
        password= request.POST.get('password','')
        user = User.objects.filter(email  = email ).first()

        if user:
            authenticated_user = authenticate(
                request,
                username = user.username,
                password = password
            )
            if authenticated_user is not None:
                login(request, authenticated_user)

                if authenticated_user.role == User.Role.ADMIN:
                    return redirect('/admin/')
            
                elif authenticated_user.role ==User.Role.WARDEN:
                    return redirect('warden_dashboard')
                else:
                    return redirect('resident_dashboard')
        messages.error(request, 'Invalid UserName or Password !! Check Your Credentials Again')
    
    return render(request, 'accounts/auth.html',{
        'form_data':{},
        'initial_panel':'signin'
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

    category_fields = {
        'STUDENT': ['institution_name', 'course', 'study_year'],
        'JOB_SEEKER': ['qualification', 'preferred_job_location'],
        'WORKING_PROFESSIONAL': ['company_name', 'designation', 'work_location'],
        'EXAM_ASPIRANT': ['exam_name', 'coaching_institute'],
        'INTERN': ['organisation', 'training_details'],
        'BUSINESS': ['business_name', 'business_type'],
        'MEDICAL': ['hospital_name', 'visit_purpose'],
        'TEMPORARY': ['stay_purpose', 'stay_duration'],
    }

    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        date_of_birth = request.POST.get('date_of_birth', '')
        gender = request.POST.get('gender', '')
        address = request.POST.get('address', '').strip()
        emergency_contact_name = request.POST.get('emergency_contact_name', '').strip()
        emergency_contact_number = request.POST.get('emergency_contact_number', '').strip()
        category = request.POST.get('category', '')

        errors = []

        if not all([
            full_name, phone_number, date_of_birth, gender,
            address, emergency_contact_name,
            emergency_contact_number, category
        ]):
            errors.append('Please fill in all required fields.')

        dob = parse_date(date_of_birth)

        if date_of_birth and not dob:
            errors.append('Please enter a valid date of birth.')

        if gender not in User.Gender.values:
            errors.append('Please select a valid gender.')

        if category not in User.Category.values:
            errors.append('Please select a valid resident category.')

        category_details = {}

        if category in category_fields:
            for field in category_fields[category]:
                value = request.POST.get(field, '').strip()

                if not value:
                    errors.append(f'{field.replace("_", " ").title()} is required.')

                category_details[field] = value

        if not errors:
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

            messages.success(request, 'Your profile has been completed successfully!')
            return redirect('resident_dashboard')

        for error in errors:
            messages.error(request, error)

    return render(request, 'accounts/complete_profile.html', {
        'user': user,
        'category_choices': User.Category.choices,
        'gender_choices': User.Gender.choices,
    })
