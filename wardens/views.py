from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from properties.models import Room, Bed
from allocations.models import Allocation
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST
from django.db.models import Prefetch
from reservations.models import AccommodationRequest
from django.utils import timezone
from django.views.decorators.http import require_POST
from reservations.models import Reservation
from payments.models import RentAdvance
from payments.services import create_first_month_fee
from payments.models import Fee, Payment
from django.db.models import Sum
from decimal import Decimal
from payments.models import OnlinePaymentOrder
from payments.razorpay_service import create_razorpay_order
from decimal import  InvalidOperation
from django.views.decorators.http import require_POST
from django.db import transaction
from payments.razorpay_service import get_razorpay_client
from payments.services import record_verified_online_payment
import json
import hmac
import hashlib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings




import logging

logger = logging.getLogger(__name__)





# Create your views here.
@login_required
def warden_dashboard(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')
    total_residents = User.objects.filter(is_active=True, role=User.Role.RESIDENT).count()
    total_rooms=Room.objects.count()
    occupied_beds =Allocation.objects.filter(is_active=True).count()

    available_beds= Bed.objects.count()
    resident_categories = (
        User.objects.filter(role=User.Role.RESIDENT)
        .values('category__name')
        .annotate(total=Count('id'))
        .order_by('category__name')
    )

    category_labels = [
        item['category__name'] or 'Other'
        for item in resident_categories
    ]

    category_counts = [
        item['total']
        for item in resident_categories
    ]

    
    context = {
        'total_residents': total_residents,
        'total_rooms': total_rooms,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
        'bed_chart_data': {
                        'labels': ['Occupied Beds', 'Available Beds'],
                        'series': [occupied_beds, available_beds],
                    },
        'category_chart_data': {
                        'labels': category_labels,
                        'series': category_counts,
                    },
    }

    return render(request, 'wardens/dashboard.html', context)


@login_required
def resident_list(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    
    residents = User.objects.filter(
    role=User.Role.RESIDENT ).select_related('category').order_by('full_name', 'id')
    search_query = request.GET.get('search', '').strip()

    if search_query:
        residents = residents.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )

    # Allow only 10 or 15 records per page
    per_page = request.GET.get('per_page', '10')

    if per_page not in ['10', '15' , '25'  , '50']:
        per_page = '10'

    paginator = Paginator(residents, int(per_page))
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'residents': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'per_page': per_page,
        'total_residents': paginator.count,
    }

    return render(request, 'wardens/resident_list.html', context)

@login_required
def resident_detail(request, resident_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    resident = get_object_or_404(
        User,
        id=resident_id,
        role=User.Role.RESIDENT
    )
    category_details = resident.category_details or {}

    category_fields = []

    if resident.category:
        fields = resident.category.custom_fields.all()

        for field in fields:
            if field.field_key in category_details:
                category_fields.append({
                    'label': field.label,
                    'value': category_details[field.field_key],
                })

    active_allocation = resident.allocations.filter(
        is_active=True
    ).select_related(
        'bed',
        'bed__room',
        'bed__room__floor',
        'bed__room__floor__building'
    ).first()

    context = {
        'resident': resident,
        'active_allocation': active_allocation,
        'category_fields': category_fields,
    }

    return render(request, 'wardens/resident_detail.html', context)


@login_required
def allocation_list(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    allocations = Allocation.objects.filter(
        is_active=True
    ).select_related(
        'resident',
        'bed',
        'bed__room',
        'bed__room__floor',
        'bed__room__floor__building'
    ).order_by('-allocated_on')

    search_query = request.GET.get('search', '').strip()

    if search_query:
        allocations = allocations.filter(
            Q(resident__full_name__icontains=search_query) |
            Q(resident__email__icontains=search_query) |
            Q(bed__room__room_number__icontains=search_query) |
            Q(bed__bed_number__icontains=search_query)
        )

    per_page = request.GET.get('per_page', '10')

    if per_page not in ['10', '15', '25', '50']:
        per_page = '10'

    paginator = Paginator(allocations, int(per_page))
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'allocations': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'per_page': per_page,
        'total_allocations': paginator.count,
    }

    return render(request, 'wardens/allocation_list.html', context)


@login_required
def allocate_bed(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    residents = User.objects.filter(
        role=User.Role.RESIDENT,
        is_active=True
    ).exclude(
        allocations__is_active=True
    ).order_by('full_name')

    available_beds = Bed.objects.exclude(
        allocations__is_active=True
    ).select_related(
        'room',
        'room__floor',
        'room__floor__building'
    )

    if request.method == 'POST':
        resident_id = request.POST.get('resident')
        bed_id = request.POST.get('bed')
        payment_method = request.POST.get('payment_method')

        resident = get_object_or_404(residents, id=resident_id)
        bed = get_object_or_404(available_beds, id=bed_id)

        if payment_method not in [
            'CASH', 'UPI', 'BANK_TRANSFER'
        ]:
            messages.error(request, 'Select a valid payment method.')
        else:
            try:
                with transaction.atomic():
                    allocation = Allocation(
                        resident=resident,
                        bed=bed,
                        is_active=True
                    )
                    allocation.full_clean()
                    allocation.save()
                    RentAdvance.objects.create(
                        allocation=allocation,
                        amount=bed.monthly_rent,
                        payment_method=payment_method,
                        received_by=request.user,
                        is_paid=True,
                        paid_at=timezone.now()
                    )
                    create_first_month_fee(allocation)

                messages.success(
                    request,
                    f'{resident.full_name or resident.username} '
                    f'has been allocated successfully. '
                    f'Advance of ₹{bed.monthly_rent} recorded.'
                )

                return redirect('warden_allocation_list')

            except (ValidationError, IntegrityError):
                messages.error(
                    request,
                    'Allocation failed. The resident or bed may already be allocated.'
                )

    context = {
        'residents': residents,
        'available_beds': available_beds,
        'unallocated_residents_count': residents.count(),
        'available_beds_count': available_beds.count(),
    }

    return render(
        request,
        'wardens/allocate_bed.html',
        context
    )


@login_required
@require_POST
def vacate_bed(request, allocation_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    allocation = get_object_or_404(
        Allocation,
        id=allocation_id,
        is_active=True
    )

    allocation.is_active = False
    allocation.vacated_on = timezone.localdate()
    allocation.save(update_fields=['is_active', 'vacated_on'])

    resident_name = (
    allocation.resident.full_name
    or allocation.resident.username
    )

    messages.success(
        request,
        f'{resident_name} has vacated the bed successfully.'
    )

    return redirect('warden_allocation_list')



@login_required
def room_list(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    rooms = Room.objects.select_related(
        'floor',
        'floor__building'
    ).annotate(
        total_beds=Count('beds', distinct=True),
        occupied_beds=Count(
            'beds__allocations',
            filter=Q(beds__allocations__is_active=True),
            distinct=True
        )
    ).order_by(
        'floor__building__name',
        'floor__floor_number',
        'room_number',
    )

    search_query = request.GET.get('search', '').strip()

    if search_query:
        rooms = rooms.filter(
            Q(room_number__icontains=search_query) |
            Q(floor__building__name__icontains=search_query)
        )

    per_page = request.GET.get('per_page', '10')

    if per_page not in ['10', '15', '25', '50']:
        per_page = '10'

    paginator = Paginator(rooms, int(per_page))
    page_obj = paginator.get_page(request.GET.get('page'))
    for room in page_obj.object_list:
        room.available_beds = room.total_beds - room.occupied_beds
    context = {
        'rooms': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'per_page': per_page,
        'total_rooms': paginator.count,
    }

    return render(request, 'wardens/room_list.html', context)




@login_required
def room_detail(request, room_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    active_allocations = Allocation.objects.filter(
        is_active=True
    ).select_related('resident')

    room = get_object_or_404(
        Room.objects.select_related(
            'floor',
            'floor__building'
        ).prefetch_related(
            'facilities',
            Prefetch(
                'beds',
                queryset=Bed.objects.prefetch_related(
                    Prefetch(
                        'allocations',
                        queryset=active_allocations,
                        to_attr='active_allocations'
                    )
                )
            )
        ),
        id=room_id
    )

    beds = room.beds.all()
    total_beds = len(beds)

    occupied_beds = sum(
        1 for bed in beds if bed.active_allocations
    )

    available_beds = total_beds - occupied_beds

    context = {
        'room': room,
        'beds': beds,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
    }

    return render(request, 'wardens/room_detail.html', context)




@login_required
def accommodation_request_list(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    pending_requests = AccommodationRequest.objects.filter(
        status=AccommodationRequest.Status.PENDING
    ).select_related(
        'resident',
        'resident__category'
    ).order_by('-created_at')

    context = {
        'pending_requests': pending_requests,
        'total_pending': pending_requests.count(),
    }

    return render(
        request,
        'wardens/accommodation_requests.html',
        context
    )


@login_required
def accommodation_request_detail(request, request_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    accommodation_request = get_object_or_404(
        AccommodationRequest.objects.select_related(
            'resident',
            'resident__category',
            'reviewed_by'
        ),
        id=request_id
    )

    return render(
        request,
        'wardens/accommodation_request_detail.html',
        {
            'accommodation_request': accommodation_request,
        }
    )



@login_required
@require_POST
def review_accommodation_request(request, request_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    accommodation_request = get_object_or_404(
        AccommodationRequest,
        id=request_id
    )

    if accommodation_request.status != AccommodationRequest.Status.PENDING:
        messages.error(request, 'This request has already been reviewed.')
        return redirect(
            'warden_accommodation_request_detail',
            request_id=request_id
        )

    action = request.POST.get('action')

    if action == 'reject':
        accommodation_request.status = AccommodationRequest.Status.REJECTED
        accommodation_request.reviewed_by = request.user
        accommodation_request.reviewed_at = timezone.now()
        accommodation_request.save(update_fields=[
            'status', 'reviewed_by', 'reviewed_at', 'updated_at'
        ])

        messages.success(request, 'Accommodation request rejected.')

    elif action == 'approve':
        try:
            with transaction.atomic():
                # Total beds available for this room type.
                total_beds = Room.objects.filter(
                    room_type=accommodation_request.preferred_room_type
                ).aggregate(
                    total=Count('beds')
                )['total'] or 0

                # Find reservations that overlap the requested dates.
                overlapping_reservations = Reservation.objects.filter(
                    preferred_room_type=accommodation_request.preferred_room_type,
                    status=Reservation.Status.CONFIRMED,
                    check_in_date__lt=accommodation_request.expected_check_out,
                    expected_check_out__gt=accommodation_request.requested_check_in,
                )

                reserved_resident_ids = list(
                    overlapping_reservations.values_list(
                        'resident_id', flat=True
                    )
                )

                reserved_count = overlapping_reservations.count()

                # Count currently allocated residents who are not
                # already counted through an overlapping reservation.
                occupied_count = Allocation.objects.filter(
                    is_active=True,
                    bed__room__room_type=accommodation_request.preferred_room_type
                ).exclude(
                    resident_id__in=reserved_resident_ids
                ).count()

                available_capacity = total_beds - reserved_count - occupied_count

                if available_capacity <= 0:
                    messages.error(
                        request,
                        'No capacity is available for this room type during the requested dates.'
                    )
                    return redirect(
                        'warden_accommodation_request_detail',
                        request_id=request_id
                    )

                reservation = Reservation(
                    request=accommodation_request,
                    resident=accommodation_request.resident,
                    preferred_room_type=accommodation_request.preferred_room_type,
                    check_in_date=accommodation_request.requested_check_in,
                    expected_check_out=accommodation_request.expected_check_out,
                    created_by=request.user,
                )

                reservation.full_clean()
                reservation.save()

                accommodation_request.status = AccommodationRequest.Status.APPROVED
                accommodation_request.reviewed_by = request.user
                accommodation_request.reviewed_at = timezone.now()
                accommodation_request.save(update_fields=[
                    'status', 'reviewed_by', 'reviewed_at', 'updated_at'
                ])

            messages.success(
                request,
                'Request approved and reservation created successfully.'
            )

        except (ValidationError, IntegrityError) as error:
            messages.error(
                request,
                'Could not create the reservation. Please check the request and try again.'
            )

    else:
        messages.error(request, 'Invalid action.')

    return redirect(
        'warden_accommodation_request_detail',
        request_id=request_id
    )


@login_required
def payment_list(request):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    fees = Fee.objects.select_related(
        'allocation',
        'allocation__resident',
        'allocation__bed',
        'allocation__bed__room'
    ).order_by('-period_start')

    total_billed = fees.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    total_collected = Payment.objects.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    total_outstanding = total_billed - total_collected

    context = {
        'fees': fees,
        'total_billed': total_billed,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'pending_count': sum(1 for fee in fees if fee.balance > 0),
    }

    return render(
        request,
        'wardens/payment_list.html',
        context
    )



from decimal import Decimal, InvalidOperation

@login_required
def record_payment(request, fee_id):
    User = get_user_model()

    if request.user.role != User.Role.WARDEN:
        return redirect('auth')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                fee = get_object_or_404(
                    Fee.objects.select_for_update(),
                    id=fee_id
                )

                amount = Decimal(request.POST.get('amount', '0'))
                payment_method = request.POST.get('payment_method')

                transaction_ref = request.POST.get(
                    'transaction_ref', ''
                ).strip()

                notes = request.POST.get('notes', '').strip()

                if amount <= 0:
                    raise ValueError('Enter a valid payment amount.')

                if amount > fee.balance:
                    raise ValueError(
                        f'Payment cannot exceed the outstanding balance of ₹{fee.balance}.'
                    )

                if payment_method not in dict(Payment.PaymentMethod.choices):
                    raise ValueError('Select a valid payment method.')

                Payment.objects.create(
                    fee=fee,
                    amount=amount,
                    payment_method=payment_method,
                    transaction_ref=transaction_ref,
                    received_by=request.user,
                    notes=notes
                )

            messages.success(request, 'Payment recorded successfully.')
            return redirect('warden_payment_list')

        except (ValueError, InvalidOperation) as error:
            messages.error(request, str(error))

    fee = get_object_or_404(
        Fee.objects.select_related(
            'allocation__resident',
            'allocation__bed',
            'allocation__bed__room'
        ),
        id=fee_id
    )

    context = {
        'fee': fee,
        'payment_methods': Payment.PaymentMethod.choices,
    }

    return render(request, 'wardens/record_payment.html', context)



from django.conf import settings

@login_required
def create_payment_order(request, fee_id):
    User = get_user_model()

    if request.user.role != User.Role.RESIDENT:
        return redirect('auth')

    fee = get_object_or_404(
        Fee.objects.select_related('allocation__resident'),
        id=fee_id,
        allocation__resident=request.user
    )

    if request.method == 'POST':
        try:
            payment_type = request.POST.get('payment_type')

            if fee.balance <= 0:
                raise ValueError('This rent bill is already paid.')

            if payment_type == 'FULL':
                amount = fee.balance

            elif payment_type == 'PARTIAL':
                amount = Decimal(request.POST.get('amount', '0'))

            else:
                raise ValueError('Select a valid payment type.')

            amount = amount.quantize(Decimal('0.01'))

            if amount <= 0:
                raise ValueError('Enter a valid payment amount.')

            if amount > fee.balance:
                raise ValueError(
                    'Payment cannot exceed the outstanding balance.'
                )

            order = create_razorpay_order(amount, fee.id)

            OnlinePaymentOrder.objects.create(
                fee=fee,
                amount=amount,
                razorpay_order_id=order['id']
            )

            context = {
                'fee': fee,
                'order_id': order['id'],
                'amount': amount,
                'order_amount': order['amount'],
                'key_id': settings.RAZORPAY_KEY_ID,
            }
            return render(
                request,
                'residents/payment_checkout.html',
                context
            )

        except (ValueError, InvalidOperation) as error:
            messages.error(request, str(error))

    return render(
        request,
        'residents/create_payment.html',
        {'fee': fee}
    )

@login_required
@require_POST
def verify_razorpay_payment(request):
    User = get_user_model()

    if request.user.role != User.Role.RESIDENT:
        return redirect('auth')

    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    if not all([
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature
    ]):
        messages.error(request, 'Payment verification details are missing.')
        return redirect('resident_dashboard')

    client = get_razorpay_client()

    try:
        with transaction.atomic():
            online_order = get_object_or_404(
                OnlinePaymentOrder.objects.select_for_update(),
                razorpay_order_id=razorpay_order_id,
                fee__allocation__resident=request.user
            )
            fee_id = online_order.fee_id

            if online_order.status == OnlinePaymentOrder.Status.PAID:
                messages.info(request, 'This payment has already been recorded.')
                return redirect(
                    'resident_create_payment_order',
                    fee_id=online_order.fee_id
                )

            if online_order.status != OnlinePaymentOrder.Status.CREATED:
                raise ValueError('This payment order is no longer active.')

            # Verify Razorpay's checkout signature.
            client.utility.verify_payment_signature({
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature,
            })

            # Confirm the payment is captured and belongs to this order.
            razorpay_payment = client.payment.fetch(razorpay_payment_id)

            if razorpay_payment['order_id'] != razorpay_order_id:
                raise ValueError('Payment does not match this order.')

            if razorpay_payment['status'] != 'captured':
                raise ValueError('Payment has not been captured yet.')

            expected_amount = int(online_order.amount * 100)

            if razorpay_payment['amount'] != expected_amount:
                raise ValueError('Payment amount does not match the rent bill.')

            if razorpay_payment['currency'] != 'INR':
                raise ValueError('Invalid payment currency.')

            method_mapping = {
                'upi': Payment.PaymentMethod.UPI,
                'card': Payment.PaymentMethod.CARD,
                'netbanking': Payment.PaymentMethod.BANK_TRANSFER,
            }

            payment_method = method_mapping.get(
                razorpay_payment['method']
            )

            if not payment_method:
                raise ValueError('This payment method is not supported yet.')

            record_verified_online_payment(
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                payment_method=payment_method
            )

            online_order.status = OnlinePaymentOrder.Status.PAID
            online_order.save(update_fields=['status'])

        messages.success(request, 'Payment verified and recorded successfully.')

        return redirect(
            'resident_create_payment_order',
            fee_id=online_order.fee_id
        )

    except Exception:
        messages.error(
            request,
            'Payment verification failed. If money was deducted, please contact the Warden.'
        )

        if fee_id:
            return redirect(
                'resident_create_payment_order',
                fee_id=fee_id
            )

        return redirect('resident_dashboard')


