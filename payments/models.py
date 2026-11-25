from django.db import models

# Create your models here.

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum
from django.core.validators import MinValueValidator
from allocations.models import Allocation


class Fee(models.Model):

    allocation = models.ForeignKey(
        Allocation,
        on_delete=models.PROTECT,
        related_name='fees'
    )

    period_start = models.DateField()
    period_end = models.DateField()
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-period_start']
        constraints = [
            models.UniqueConstraint(
                fields=['allocation', 'period_start'],
                name='unique_fee_per_allocation_period'
            )
        ]

    @property
    def total_paid(self):
        result = self.payments.aggregate(
            total=Sum('amount')
        )['total']
        return result or 0

    @property
    def balance(self):
        return self.amount - self.total_paid

    
        @property
        def status(self):
            if self.balance <= 0:
                return 'PAID'

            if self.total_paid > 0:
                deadline = self.due_date.replace(day=10)

                if timezone.localdate() > deadline:
                    return 'OVERDUE'

                return 'PARTIALLY_PAID'

            if timezone.localdate() > self.due_date:
                return 'OVERDUE'

            return 'PENDING'

        def __str__(self):
            return f"{self.allocation.resident} - {self.period_start}"

class Payment(models.Model):

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        UPI = 'UPI', 'UPI'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        CARD = 'CARD', 'Card'

    fee = models.ForeignKey(
        Fee,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices
    )

    transaction_ref = models.CharField(
        max_length=100,
        blank=True
    )

    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_payments',
        null=True,
        blank=True
    )
    paid_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.fee} - ₹{self.amount}"


class RentAdvance(models.Model):

    class SettlementChoice(models.TextChoices):
        REFUND = 'REFUND', 'Refund'
        ADJUSTMENT = 'ADJUSTMENT', 'Adjust Against Final Rent'

    allocation = models.OneToOneField(
        Allocation,
        on_delete=models.PROTECT,
        related_name='rent_advance'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    paid_on = models.DateField(default=timezone.localdate)

    settlement_choice = models.CharField(
        max_length=20,
        choices=SettlementChoice.choices,
        blank=True
    )

    adjusted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    refunded_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    settled_on = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)



    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        UPI = 'UPI', 'UPI'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'

    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True
    )
    
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='received_advances',
        null=True,
        blank=True
    )

    is_paid = models.BooleanField(default=False)

    paid_at = models.DateTimeField(null=True, blank=True)

    @property
    def remaining_amount(self):
        return self.amount - self.adjusted_amount - self.refunded_amount

    def __str__(self):
        return f"{self.allocation.resident} - Advance ₹{self.amount}"



    
class OnlinePaymentOrder(models.Model):

    class Status(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        PAID = 'PAID', 'Paid'
        FAILED = 'FAILED', 'Failed'

    fee = models.ForeignKey(
        Fee,
        on_delete=models.PROTECT,
        related_name='online_orders'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    razorpay_order_id = models.CharField(
        max_length=100,
        unique=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.fee} - {self.razorpay_order_id}"