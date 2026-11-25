
from calendar import monthrange
from datetime import date,timezone
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from .models import Fee, Payment, OnlinePaymentOrder




def create_first_month_fee(allocation):
    allocation_date = allocation.allocated_on

    days_in_month = monthrange(
        allocation_date.year,
        allocation_date.month
    )[1]

    occupied_days = days_in_month - allocation_date.day + 1

    monthly_rent = allocation.bed.monthly_rent

    daily_rent = monthly_rent / Decimal(days_in_month)

    amount = (
        daily_rent * Decimal(occupied_days)
    ).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )

    period_end = date(
        allocation_date.year,
        allocation_date.month,
        days_in_month
    )

    if allocation_date.month == 12:
        due_date = date(allocation_date.year + 1, 1, 5)
    else:
        due_date = date(
            allocation_date.year,
            allocation_date.month + 1,
            5
        )

    fee, created = Fee.objects.get_or_create(
        allocation=allocation,
        period_start=allocation_date.replace(day=1),
        defaults={
            'period_end': period_end,
            'amount': amount,
            'due_date': due_date,
        }
    )

    return fee



def generate_monthly_fees(billing_date=None):
    from calendar import monthrange
    from datetime import date

    from allocations.models import Allocation

    if billing_date is None:
        billing_date = timezone.localdate()

    days_in_month = monthrange(
        billing_date.year,
        billing_date.month
    )[1]

    # Only generate bills on the last day of the month.
    billing_day = min(30, days_in_month)

    if billing_date.day != billing_day:
        raise ValueError(
            "Monthly bills can only be generated on the last day of the month."
        )

    period_start = date(
        billing_date.year,
        billing_date.month,
        1
    )

    period_end = date(
        billing_date.year,
        billing_date.month,
        days_in_month
    )

    # Due date is the 5th of the following month.
    if billing_date.month == 12:
        due_date = date(billing_date.year + 1, 1, 5)
    else:
        due_date = date(
            billing_date.year,
            billing_date.month + 1,
            5
        )

    allocations = Allocation.objects.filter(
        is_active=True,
        allocated_on__lte=period_end
    ).select_related('bed')

    created_count = 0

    for allocation in allocations:
        fee, created = Fee.objects.get_or_create(
            allocation=allocation,
            period_start=period_start,
            defaults={
                'period_end': period_end,
                'amount': allocation.bed.monthly_rent,
                'due_date': due_date,
            }
        )

        if created:
            created_count += 1

    return created_count




@transaction.atomic
def record_verified_online_payment(
    razorpay_order_id,
    razorpay_payment_id,
    payment_method
):
    online_order = OnlinePaymentOrder.objects.select_for_update().get(
        razorpay_order_id=razorpay_order_id
    )

    if online_order.status == OnlinePaymentOrder.Status.PAID:
        if online_order.razorpay_payment_id == razorpay_payment_id:
            return False

        raise ValueError('This order has already been paid.')

    if online_order.status != OnlinePaymentOrder.Status.CREATED:
        raise ValueError('This order is not available for payment.')

    fee = Fee.objects.select_for_update().get(
        id=online_order.fee_id
    )

    # Prevent payment from exceeding the remaining balance.
    if online_order.amount > fee.balance:
        raise ValueError('Payment exceeds the outstanding balance.')

    # Prevent the same Razorpay transaction from being recorded twice.
    if Payment.objects.filter(
        transaction_ref=razorpay_payment_id
    ).exists():
        raise ValueError('This transaction has already been recorded.')

    Payment.objects.create(
        fee=fee,
        amount=online_order.amount,
        payment_method=payment_method,
        transaction_ref=razorpay_payment_id,
        received_by=None,
        notes='Online payment through Razorpay.'
    )

    online_order.razorpay_payment_id = razorpay_payment_id
    online_order.status = OnlinePaymentOrder.Status.PAID

    online_order.save(update_fields=[
        'razorpay_payment_id',
        'status'
    ])

    return True
