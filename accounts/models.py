from django.db import models
from django.contrib.auth.models import AbstractUser , UserManager

# Create your models here.

class CustomUserManager(UserManager):
    def create_superuser(self,username, email=None, password = None, **extra_fields):
        extra_fields.setdefault('role','ADMIN')

        return super().create_superuser(
            username,
            email,
            password,
            **extra_fields
        )


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN       =   "ADMIN","Admin"
        WARDEN      =   "WARDEN" , "Warden"
        RESIDENT    =   "RESIDENT" ,"Resident"

    class Category(models.TextChoices):
        STUDENT = "STUDENT", "Students"
        JOB_SEEKER = "JOB_SEEKER", "Job Seekers"
        WORKING_PROFESSIONAL = "WORKING_PROFESSIONAL", "Working Professionals"
        EXAM_ASPIRANT = "EXAM_ASPIRANT", "Exam Aspirants"
        INTERN = "INTERN", "Interns & Trainees"
        BUSINESS = "BUSINESS", "Business Professionals"
        MEDICAL = "MEDICAL", "Medical Visitors"
        TEMPORARY = "TEMPORARY", "Temporary Residents"
        OTHER = "OTHER", "Others"
    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Others"

    email = models.EmailField(unique=True)

    phone_number =  models.CharField(
        max_length=15,
        blank = True
        )
    role = models.CharField(
        max_length=20,
        choices= Role.choices ,
        default=Role.RESIDENT
        )

    full_name = models.CharField(max_length=150, blank=True)

    date_of_birth = models.DateField(null= True , blank= True)

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True
        )

    address = models.TextField(blank=True)

    emergency_contact_name = models.CharField(max_length=50 , blank = True)
    emergency_contact_number= models.CharField(max_length=15 , blank= True) 

    category = models.CharField(
        max_length=30 , 
        choices = Category.choices , 
        blank = True
    )
    
    other_category = models.CharField(max_length=150 , blank=True) 

    #category details saved as JSONB format so we can retrieve without being creating a new table or relation
    category_details = models.JSONField(default=dict, blank=True)


    objects= CustomUserManager()
    def __str__(self):
        return f"{self.username} - {self.role}"