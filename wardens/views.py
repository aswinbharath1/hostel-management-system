from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from properties.models import Room, Bed
from allocations.models import Allocation
from django.db.models import Q, Count
from django.core.paginator import Paginator
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
    .values('category')
    .annotate(total=Count('id'))
    .order_by('category')
    )

    category_labels = [
        dict(User.Category.choices).get(item['category'], 'Other')
        for item in resident_categories
    ]

    category_counts = [
        item['total'] for item in resident_categories
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
        role=User.Role.RESIDENT
    ).order_by('full_name', 'id')

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
