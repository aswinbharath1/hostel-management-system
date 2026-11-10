
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()
# Create your views here.
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
        category = request.POST.get('category','')

        password1= request.POST.get('password1','').strip()
        password2= request.POST.get('password2','').strip()

        other_category= request.POST.get('other_category','').strip()

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
            'OTHER': [
                'other_purpose'
            ]
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
                    category=category,
                    other_category=other_category,
                    category_details=category_details
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

# def login_view(request):
#     if request.method=='POST':
#         username= request.POST.get('username','').strip()
#         password= request.POST.get('password','')
    
