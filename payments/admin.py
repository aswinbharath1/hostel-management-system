from django.contrib import admin

# Register your models here.

from django.contrib import admin
from .models import Fee, Payment, RentAdvance


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = (
        'allocation',
        'period_start',
        'period_end',
        'amount',
        'due_date',
    )
    list_filter = ('due_date',)
    search_fields = ('allocation__resident__username',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'fee',
        'amount',
        'payment_method',
        'paid_at',
        'received_by',
    )
    list_filter = ('payment_method', 'paid_at')


@admin.register(RentAdvance)
class RentAdvanceAdmin(admin.ModelAdmin):
    list_display = (
        'allocation',
        'amount',
        'settlement_choice',
        'adjusted_amount',
        'refunded_amount',
    )
