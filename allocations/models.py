
from django.db import models
from django.conf import settings
from django.db.models import Q
from properties.models import Bed
from django.core.exceptions import ValidationError


class Allocation(models.Model):

    resident = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='allocations'
    )

    bed = models.ForeignKey(
        Bed,
        on_delete=models.PROTECT,
        related_name='allocations'
    )

    allocated_on = models.DateField(auto_now_add=True)
    vacated_on = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-allocated_on']

        constraints = [
            models.UniqueConstraint(
                fields=['resident'],
                condition=Q(is_active=True),
                name='unique_active_allocation_per_resident'
            ),
            models.UniqueConstraint(
                fields=['bed'],
                condition=Q(is_active=True),
                name='unique_active_allocation_per_bed'
            ),
        ]

    def __str__(self):
        return f"{self.resident} - {self.bed}"

    
    def clean(self):
        if self.resident.role != 'RESIDENT':
            raise ValidationError({
                'resident': 'Only residents can receive bed allocations.'
            })

        if self.is_active:
            existing = Allocation.objects.filter(
                is_active=True
            ).exclude(pk=self.pk)

            if existing.filter(resident=self.resident).exists():
                raise ValidationError({
                    'resident': 'This resident already has an active allocation.'
                })

            if existing.filter(bed=self.bed).exists():
                raise ValidationError({
                    'bed': 'This bed is already occupied.'
                })