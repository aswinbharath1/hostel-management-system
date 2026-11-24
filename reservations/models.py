from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from properties.models import Room


class AccommodationRequest(models.Model):

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='accommodation_requests'
    )

    preferred_room_type = models.CharField(
        max_length=20,
        choices=Room.RoomType.choices
    )

    requested_check_in = models.DateField()
    expected_check_out = models.DateField()

    additional_notes = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_accommodation_requests'
    )

    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.requested_check_in and self.expected_check_out:
            if self.expected_check_out <= self.requested_check_in:
                raise ValidationError({
                    'expected_check_out':
                    'Expected check-out must be after check-in.'
                })

        if self.resident and self.resident.role != 'RESIDENT':
            raise ValidationError({
                'resident': 'Only residents can submit accommodation requests.'
            })

    def __str__(self):
        return f"{self.resident} - {self.get_status_display()}"


class Reservation(models.Model):

    class Status(models.TextChoices):
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        COMPLETED = 'COMPLETED', 'Completed'
        EXPIRED = 'EXPIRED', 'Expired'

    request = models.OneToOneField(
        AccommodationRequest,
        on_delete=models.PROTECT,
        related_name='reservation'
    )

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='reservations'
    )

    preferred_room_type = models.CharField(
        max_length=20,
        choices=Room.RoomType.choices
    )

    check_in_date = models.DateField()
    expected_check_out = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CONFIRMED
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_reservations'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.check_in_date and self.expected_check_out:
            if self.expected_check_out <= self.check_in_date:
                raise ValidationError({
                    'expected_check_out':
                    'Expected check-out must be after check-in.'
                })

        if self.request_id and self.resident_id:
            if self.request.resident_id != self.resident_id:
                raise ValidationError(
                    'Reservation resident must match the accommodation request.'
                )

    def __str__(self):
        return f"Reservation - {self.resident} ({self.get_status_display()})"
