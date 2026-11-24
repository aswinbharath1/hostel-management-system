
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')

        return super().create_superuser(
            username,
            email,
            password,
            **extra_fields
        )


class ResidentCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Resident Categories'

    def __str__(self):
        return self.name



class ResidentCategoryField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        NUMBER = 'NUMBER', 'Number'
        DATE = 'DATE', 'Date'
        TEXTAREA = 'TEXTAREA', 'Textarea'

    category = models.ForeignKey(
        ResidentCategory,
        on_delete=models.CASCADE,
        related_name='custom_fields'
    )
    label = models.CharField(max_length=100)
    field_key = models.SlugField(max_length=100)
    field_type = models.CharField(
        max_length=20,
        choices=FieldType.choices,
        default=FieldType.TEXT
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'label']
        unique_together = ('category', 'field_key')

    def __str__(self):
        return f'{self.category.name} - {self.label}'



class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        WARDEN = "WARDEN", "Warden"
        RESIDENT = "RESIDENT", "Resident"

    class Gender(models.TextChoices):
        MALE = "MALE", "Male"
        FEMALE = "FEMALE", "Female"
        OTHER = "OTHER", "Others"

    email = models.EmailField(unique=True)

    phone_number = models.CharField(max_length=15, blank=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.RESIDENT
    )

    full_name = models.CharField(max_length=150, blank=True)

    date_of_birth = models.DateField(null=True, blank=True)

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True
    )

    address = models.TextField(blank=True)

    emergency_contact_name = models.CharField(max_length=50, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)

    category = models.ForeignKey(
        ResidentCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='residents'
    )

    category_details = models.JSONField(default=dict, blank=True)
    profile_completed = models.BooleanField(default=False)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} - {self.role}"
