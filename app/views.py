import json
import urllib.parse
from decimal import Decimal
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Count
from .models import Trip, TripStop, Itinerary, ItineraryItem, City
from .ai_helper import (
    search_cities_ai,
    fetch_activities_for_city_ai,
    generate_ai_itinerary_rupees,
    generate_smart_budget_rupees
)

# -------------------------------------------------------------------------
# HOME & DASHBOARD
# -------------------------------------------------------------------------
@login_required
def home_view(request):
    today = timezone.now().date()
    user_trips = Trip.objects.filter(user=request.user)

    upcoming_trips = user_trips.filter(start_date__gt=today).order_by('start_date')
    ongoing_trips = user_trips.filter(start_date__lte=today, end_date__gte=today).order_by('start_date')
    completed_trips = user_trips.filter(end_date__lt=today).order_by('-end_date')[:3]
    recent_trips = user_trips.order_by('-created_at')[:4]

    trip_draft = request.session.get('trip_draft', None)
    community_trips = Trip.objects.filter(is_public=True).exclude(user=request.user).order_by('-created_at')[:3]
    total_spent = sum(t.total_cost for t in user_trips)

    context = {
        'saved_trips': user_trips,
        'total_trips': user_trips.count(),
        'ongoing_trips': ongoing_trips,
        'upcoming_trips': upcoming_trips,
        'completed_trips': completed_trips,
        'recent_trips': recent_trips,
        'trip_draft': trip_draft,
        'community_trips': community_trips,
        'total_spent': total_spent,
    }
    return render(request, 'home.html', context)


# -------------------------------------------------------------------------
# STEP-BY-STEP MULTI-CITY & AI PLANNER (STEP 1 & STEP 2 & FINAL PLAN)
# -------------------------------------------------------------------------
@login_required
def start_trip(request):
    """
    Step 1: Set Trip Details, Dates, Budget (₹), and Add Any Personalized Destinations via AI Search
    """
    if 'trip_draft' not in request.session:
        request.session['trip_draft'] = {
            'name': '',
            'start_date': '',
            'end_date': '',
            'budget': '15000',
            'description': '',
            'is_public': False,
            'cities': []
        }

    trip_draft = request.session['trip_draft']
    search_results = []
    query = request.GET.get('city_query', '').strip()

    # Dynamic AI City / Destination Search (e.g. Dwarka, Somnath, Varanasi, Manali...)
    if query:
        ai_cities = search_cities_ai(query)
        search_results = [{'display_name': c} for c in ai_cities]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save_dates':
            trip_draft['name'] = request.POST.get('name', '').strip()
            trip_draft['start_date'] = request.POST.get('start_date', '')
            trip_draft['end_date'] = request.POST.get('end_date', '')
            trip_draft['budget'] = request.POST.get('budget', '15000')
            trip_draft['description'] = request.POST.get('description', '')
            trip_draft['is_public'] = request.POST.get('is_public') == 'on'

        elif action == 'add_city':
            city_name = request.POST.get('city_name', '').strip()
            if city_name and city_name not in trip_draft['cities']:
                trip_draft['cities'].append(city_name)
                messages.success(request, f"Added '{city_name}' to destinations!")

        elif action == 'remove_city':
            city_name = request.POST.get('city_name', '').strip()
            if city_name in trip_draft['cities']:
                trip_draft['cities'].remove(city_name)
                # Also remove from events if present
                if 'events' in trip_draft and city_name in trip_draft['events']:
                    del trip_draft['events'][city_name]
                messages.info(request, f"Removed '{city_name}'.")

        request.session['trip_draft'] = trip_draft
        request.session.modified = True
        return redirect('start_trip')

    context = {
        'trip_draft': trip_draft,
        'search_results': search_results,
        'query': query,
    }
    return render(request, 'create_step1.html', context)


@login_required
def step2_events(request):
    """
    Step 2: AI dynamically fetches authentic places, temples, activities for each city in draft.
    User selects checkboxes or adds custom activities with costs in ₹ INR.
    """
    trip_draft = request.session.get('trip_draft')

    if not trip_draft or not trip_draft.get('cities'):
        messages.warning(request, "Please add at least one destination first.")
        return redirect('start_trip')

    if 'events' not in trip_draft:
        trip_draft['events'] = {}

    # Find first city that hasn't had activities chosen yet
    current_city = None
    for city in trip_draft['cities']:
        if city not in trip_draft['events']:
            current_city = city
            break

    # If all cities have chosen events, move to finalize trip
    if not current_city:
        return redirect('step3_final_plan')

    # Fetch dynamic real activities from AI for this specific city
    activities = fetch_activities_for_city_ai(current_city)

    if request.method == 'POST':
        selected_events = request.POST.getlist('selected_events')
        custom_act = request.POST.get('custom_activity', '').strip()
        custom_cost = request.POST.get('custom_cost', '200').strip()

        event_items = []
        for act in activities:
            if act.get('name') in selected_events:
                event_items.append(act)

        # Include custom added activity if user entered one
        if custom_act:
            event_items.append({
                'name': custom_act,
                'category': 'sightseeing',
                'estimated_cost': float(custom_cost) if custom_cost else 200,
                'duration': '2 hours',
                'description': 'Custom added activity.'
            })

        # If user checked items that weren't in dict, add basic objects
        for s in selected_events:
            if not any(e['name'] == s for e in event_items):
                event_items.append({
                    'name': s,
                    'category': 'sightseeing',
                    'estimated_cost': 250,
                    'duration': '2 hours',
                    'description': f'Sightseeing in {current_city}'
                })

        trip_draft['events'][current_city] = event_items
        request.session['trip_draft'] = trip_draft
        request.session.modified = True

        messages.success(request, f"Saved activities for {current_city}!")
        return redirect('step2_events')

    context = {
        'city': current_city,
        'activities': activities,
        'trip_draft': trip_draft,
    }
    return render(request, 'create_step2.html', context)


@login_required
def step3_final_plan(request):
    """
    Step 3: Builds the final relational Trip, TripStop, Itinerary days, and ItineraryItem objects in SQLite.
    """
    trip_draft = request.session.get('trip_draft')
    if not trip_draft or not trip_draft.get('cities'):
        return redirect('start_trip')

    try:
        start_date = datetime.strptime(trip_draft.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(trip_draft.get('end_date'), '%Y-%m-%d').date()
    except Exception:
        start_date = timezone.now().date() + timedelta(days=7)
        end_date = start_date + timedelta(days=len(trip_draft.get('cities', [1])) * 2 - 1)

    budget_val = Decimal(str(trip_draft.get('budget') or 15000))
    trip_name = trip_draft.get('name') or f"Journey across {', '.join(trip_draft['cities'])}"

    # 1. Create Trip Record
    trip = Trip.objects.create(
        user=request.user,
        name=trip_name,
        description=trip_draft.get('description') or f"Multi-city itinerary visiting {', '.join(trip_draft['cities'])}.",
        start_date=start_date,
        end_date=end_date,
        estimated_budget=budget_val,
        is_public=trip_draft.get('is_public', False)
    )

    # 2. Create Trip Stops
    for idx, city in enumerate(trip_draft['cities'], start=1):
        TripStop.objects.create(trip=trip, city_name=city, order=idx)

    # 3. Create Day-by-Day Itineraries from selected events
    total_days = trip.duration_days
    cities_count = len(trip_draft['cities'])
    days_per_city = max(1, total_days // cities_count)

    times = ["08:30 AM", "11:30 AM", "03:00 PM", "06:30 PM", "08:30 PM"]
    day_counter = 1

    for city in trip_draft['cities']:
        city_events = trip_draft.get('events', {}).get(city, [])
        if not city_events:
            city_events = fetch_activities_for_city_ai(city)

        # Distribute city events across days for this city
        for d in range(days_per_city):
            if day_counter > total_days:
                break
            
            day_date = start_date + timedelta(days=day_counter - 1)
            itin = Itinerary.objects.create(
                trip=trip,
                day_number=day_counter,
                date=day_date,
                city_name=city,
                title=f"{city} Exploration & Sights",
                notes=f"Exploring key highlights of {city}.",
                allocated_budget=round(budget_val / total_days, 2)
            )

            # Assign 2-3 events to this day
            sub_events = city_events[d*2 : (d+1)*2] if city_events else []
            if not sub_events and city_events:
                sub_events = city_events[:2]

            for a_idx, act in enumerate(sub_events):
                cost_val = act.get('estimated_cost', 200)
                ItineraryItem.objects.create(
                    itinerary=itin,
                    name=act.get('name', 'Sightseeing Stop'),
                    category=act.get('category', 'sightseeing'),
                    time=times[a_idx % len(times)],
                    estimated_cost=Decimal(str(cost_val)),
                    description=act.get('description', '')
                )
            day_counter += 1

    # Clear draft session
    if 'trip_draft' in request.session:
        del request.session['trip_draft']
        request.session.modified = True

    messages.success(request, f"🎉 Trip '{trip.name}' created successfully with personalized AI itinerary!")
    return redirect('itinerary_builder', trip_id=trip.id)


# -------------------------------------------------------------------------
# TRIP VIEWS & ITINERARY BUILDER
# -------------------------------------------------------------------------
@login_required
def trip_list_view(request):
    today = timezone.now().date()
    all_trips = Trip.objects.filter(user=request.user)

    query = request.GET.get('q', '').strip()
    if query:
        all_trips = all_trips.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(stops__city_name__icontains=query)
        ).distinct()

    ongoing = [t for t in all_trips if t.status == 'Ongoing']
    upcoming = [t for t in all_trips if t.status == 'Upcoming']
    completed = [t for t in all_trips if t.status == 'Completed']

    context = {
        'ongoing_trips': ongoing,
        'upcoming_trips': upcoming,
        'completed_trips': completed,
        'all_trips': all_trips,
        'query': query,
    }
    return render(request, 'trips/trip_list.html', context)


def trip_detail_or_builder(request, trip_id):
    """
    Itinerary builder & full detail view with day-wise items, costs in ₹.
    """
    trip = get_object_or_404(Trip, id=trip_id)
    is_owner = request.user.is_authenticated and trip.user == request.user

    if not is_owner and not trip.is_public:
        messages.error(request, "This trip is private.")
        return redirect('community')

    itineraries = trip.itineraries.prefetch_related('items').all()

    # Pre-fetch dynamic suggested activities for destination
    city_sample = trip.stops.first()
    suggested_acts = fetch_activities_for_city_ai(city_sample.city_name if city_sample else trip.name)

    context = {
        'trip': trip,
        'itineraries': itineraries,
        'is_owner': is_owner,
        'suggested_acts': suggested_acts,
    }
    return render(request, 'trips/itinerary_builder.html', context)


@login_required
def add_day_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        day_num = request.POST.get('day_number')
        title = request.POST.get('title', '').strip()
        city_name = request.POST.get('city_name', '').strip()
        notes = request.POST.get('notes', '').strip()

        existing_days = list(trip.itineraries.values_list('day_number', flat=True))
        try:
            day_int = int(day_num) if day_num else ((max(existing_days) + 1) if existing_days else 1)
        except Exception:
            day_int = (max(existing_days) + 1) if existing_days else 1

        if day_int in existing_days:
            day_int = max(existing_days) + 1

        date_val = trip.start_date + timedelta(days=day_int - 1) if trip.start_date else None

        Itinerary.objects.create(
            trip=trip,
            day_number=day_int,
            date=date_val,
            title=title or f"Day {day_int} Plan",
            city_name=city_name,
            notes=notes,
            allocated_budget=round(trip.estimated_budget / max(1, trip.duration_days), 2)
        )
        messages.success(request, f"Day {day_int} added.")
    return redirect('itinerary_builder', trip_id=trip.id)


@login_required
def delete_day_view(request, trip_id, day_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    day = get_object_or_404(Itinerary, id=day_id, trip=trip)
    num = day.day_number
    day.delete()
    messages.info(request, f"Day {num} removed.")
    return redirect('itinerary_builder', trip_id=trip.id)


@login_required
def add_item_view(request, trip_id, day_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    day = get_object_or_404(Itinerary, id=day_id, trip=trip)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip() or request.POST.get('custom_title', '').strip()
        category = request.POST.get('category', 'sightseeing')
        time_val = request.POST.get('time', '09:00 AM').strip()
        cost_val = request.POST.get('estimated_cost', '200').strip()
        desc = request.POST.get('notes', '').strip() or request.POST.get('description', '').strip()

        if not name:
            messages.error(request, "Please enter an activity name.")
            return redirect('itinerary_builder', trip_id=trip.id)

        try:
            cost_dec = Decimal(cost_val)
        except Exception:
            cost_dec = Decimal('200.00')

        ItineraryItem.objects.create(
            itinerary=day,
            name=name,
            category=category,
            time=time_val or "09:00 AM",
            estimated_cost=cost_dec,
            description=desc
        )
        messages.success(request, f"Added '{name}' (₹{cost_dec}) to Day {day.day_number}.")
    return redirect('itinerary_builder', trip_id=trip.id)


@login_required
def delete_item_view(request, trip_id, item_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    item = get_object_or_404(ItineraryItem, id=item_id, itinerary__trip=trip)
    name = item.name
    item.delete()
    messages.info(request, f"Removed '{name}'.")
    return redirect('itinerary_builder', trip_id=trip.id)


def trip_budget_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    is_owner = request.user.is_authenticated and trip.user == request.user

    if not is_owner and not trip.is_public:
        messages.error(request, "This trip is private.")
        return redirect('community')

    itineraries = trip.itineraries.prefetch_related('items').all()

    category_totals = {
        'sightseeing': Decimal('0.00'),
        'food': Decimal('0.00'),
        'adventure': Decimal('0.00'),
        'culture': Decimal('0.00'),
        'relaxation': Decimal('0.00'),
    }

    day_breakdowns = []
    total_cost = Decimal('0.00')

    for day in itineraries:
        day_total = Decimal('0.00')
        for item in day.items.all():
            cost = item.estimated_cost
            day_total += cost
            cat = item.category if item.category in category_totals else 'sightseeing'
            category_totals[cat] += cost

        total_cost += day_total
        day_breakdowns.append({
            'day': day,
            'cost': day_total,
            'allocated': day.allocated_budget,
            'is_over': day_total > day.allocated_budget if day.allocated_budget > 0 else False
        })

    # AI benchmark in INR
    dest_name = trip.destination_display
    ai_budget_benchmark = generate_smart_budget_rupees(dest_name, days=trip.duration_days)

    avg_cost_per_day = round(total_cost / trip.duration_days, 2) if trip.duration_days > 0 else total_cost
    remaining_budget = trip.estimated_budget - total_cost

    context = {
        'trip': trip,
        'is_owner': is_owner,
        'total_cost': total_cost,
        'remaining_budget': remaining_budget,
        'avg_cost_per_day': avg_cost_per_day,
        'category_totals': category_totals,
        'day_breakdowns': day_breakdowns,
        'ai_budget_benchmark': ai_budget_benchmark,
    }
    return render(request, 'trips/budget.html', context)


def trip_calendar_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    is_owner = request.user.is_authenticated and trip.user == request.user

    if not is_owner and not trip.is_public:
        messages.error(request, "This trip is private.")
        return redirect('community')

    itineraries = trip.itineraries.prefetch_related('items').order_by('day_number')
    calendar_days = []
    for itin in itineraries:
        calendar_days.append({
            'day_number': itin.day_number,
            'date': itin.date,
            'title': itin.title,
            'city_name': itin.city_name,
            'notes': itin.notes,
            'items': itin.items.all(),
            'total_cost': itin.day_cost
        })

    context = {
        'trip': trip,
        'is_owner': is_owner,
        'calendar_days': calendar_days,
    }
    return render(request, 'trips/calendar.html', context)


def trip_export_json_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id)
    is_owner = request.user.is_authenticated and trip.user == request.user

    if not is_owner and not trip.is_public:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    data = {
        'trip_id': trip.id,
        'name': trip.name,
        'destinations': trip.destination_display,
        'start_date': str(trip.start_date),
        'end_date': str(trip.end_date),
        'duration_days': trip.duration_days,
        'currency': 'INR',
        'target_budget': float(trip.estimated_budget),
        'total_cost': float(trip.total_cost),
        'created_by': trip.user.username,
        'itineraries': []
    }

    for itin in trip.itineraries.all():
        itin_data = {
            'day_number': itin.day_number,
            'date': str(itin.date) if itin.date else None,
            'title': itin.title,
            'city': itin.city_name,
            'day_cost': float(itin.day_cost),
            'activities': []
        }
        for item in itin.items.all():
            itin_data['activities'].append({
                'name': item.name,
                'category': item.category,
                'time': item.time,
                'cost_inr': float(item.estimated_cost),
                'description': item.description
            })
        data['itineraries'].append(itin_data)

    response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="GlobeTrotter_{trip.name.replace(" ", "_")}.json"'
    return response


@login_required
def trip_copy_view(request, trip_id):
    source_trip = get_object_or_404(Trip, id=trip_id)
    if not source_trip.is_public and source_trip.user != request.user:
        messages.error(request, "Cannot copy a private trip.")
        return redirect('community')

    new_trip = Trip.objects.create(
        user=request.user,
        name=f"Copy of {source_trip.name}",
        description=source_trip.description,
        start_date=timezone.now().date() + timedelta(days=7),
        end_date=timezone.now().date() + timedelta(days=7 + source_trip.duration_days - 1),
        estimated_budget=source_trip.estimated_budget,
        is_public=False
    )

    for stop in source_trip.stops.all():
        TripStop.objects.create(trip=new_trip, city_name=stop.city_name, order=stop.order)

    for itin in source_trip.itineraries.all():
        new_itin = Itinerary.objects.create(
            trip=new_trip,
            day_number=itin.day_number,
            date=new_trip.start_date + timedelta(days=itin.day_number - 1),
            title=itin.title,
            city_name=itin.city_name,
            notes=itin.notes,
            allocated_budget=itin.allocated_budget
        )
        for item in itin.items.all():
            ItineraryItem.objects.create(
                itinerary=new_itin,
                name=item.name,
                category=item.category,
                time=item.time,
                estimated_cost=item.estimated_cost,
                description=item.description
            )

    messages.success(request, f"Trip cloned to your account! Customize your new trip '{new_trip.name}'.")
    return redirect('itinerary_builder', trip_id=new_trip.id)


@login_required
def trip_delete_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        name = trip.name
        trip.delete()
        messages.success(request, f"Trip '{name}' deleted.")
        return redirect('trip_list')
    return render(request, 'trips/trip_confirm_delete.html', {'trip': trip})


@login_required
def trip_edit_view(request, trip_id):
    trip = get_object_or_404(Trip, id=trip_id, user=request.user)
    if request.method == 'POST':
        trip.name = request.POST.get('name', trip.name)
        trip.description = request.POST.get('description', trip.description)
        trip.start_date = request.POST.get('start_date', trip.start_date)
        trip.end_date = request.POST.get('end_date', trip.end_date)
        trip.estimated_budget = Decimal(request.POST.get('budget', trip.estimated_budget))
        trip.is_public = request.POST.get('is_public') == 'on'
        trip.save()
        messages.success(request, "Trip details updated successfully.")
        return redirect('itinerary_builder', trip_id=trip.id)
    return render(request, 'trips/trip_edit.html', {'trip': trip})


def community_view(request):
    query = request.GET.get('q', '').strip()
    public_trips = Trip.objects.filter(is_public=True).select_related('user').prefetch_related('itineraries__items', 'stops')

    if query:
        public_trips = public_trips.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(stops__city_name__icontains=query) |
            Q(user__username__icontains=query)
        ).distinct()

    context = {
        'public_trips': public_trips,
        'query': query,
    }
    return render(request, 'trips/community.html', context)


def city_search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        ai_cities = search_cities_ai(query)
        results = [{'name': c.split(',')[0], 'country': c.split(',')[1] if ',' in c else 'India', 'full': c} for c in ai_cities]

    if request.GET.get('format') == 'json':
        return JsonResponse({'cities': results})

    return render(request, 'trips/city_search.html', {'query': query, 'cities': results})


def activity_search_view(request):
    city_query = request.GET.get('city', 'Dwarka').strip()
    category_filter = request.GET.get('type', '').strip()
    activities = fetch_activities_for_city_ai(city_query)

    if category_filter:
        activities = [a for a in activities if a.get('category') == category_filter]

    user_trips = Trip.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'trips/activity_search.html', {
        'city_query': city_query,
        'activities': activities,
        'selected_type': category_filter,
        'user_trips': user_trips,
    })


def analytics_view(request):
    total_trips = Trip.objects.count()
    public_trips = Trip.objects.filter(is_public=True).count()
    total_stops = TripStop.objects.count()
    total_activities = ItineraryItem.objects.count()
    popular_stops = TripStop.objects.values('city_name').annotate(cnt=Count('city_name')).order_by('-cnt')[:6]

    context = {
        'total_trips': total_trips,
        'public_trips': public_trips,
        'private_trips': total_trips - public_trips,
        'total_stops': total_stops,
        'total_activities': total_activities,
        'popular_stops': popular_stops,
    }
    return render(request, 'trips/analytics.html', context)


# -------------------------------------------------------------------------
# REST API ENDPOINTS (AI SERVICES)
# -------------------------------------------------------------------------
@csrf_exempt
def generate_itinerary_api(request):
    """
    POST /ai/generate-itinerary/
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST if request.method == 'POST' else request.GET

    destination = data.get('destination', '').strip()
    days = data.get('number_of_days') or data.get('days', 3)
    budget = data.get('budget', 15000)
    trip_id = data.get('trip_id')

    if not destination:
        if trip_id:
            try:
                trip = Trip.objects.get(id=trip_id)
                destination = trip.destination_display
                days = trip.duration_days
                budget = trip.estimated_budget
            except Trip.DoesNotExist:
                return JsonResponse({'error': 'Trip not found'}, status=404)
        else:
            return JsonResponse({'error': 'destination parameter is required'}, status=400)

    try:
        days = int(days)
    except Exception:
        days = 3

    try:
        budget = float(budget)
    except Exception:
        budget = 15000.0

    result = generate_ai_itinerary_rupees(destination, days=days, budget_inr=budget)

    # If trip_id is provided, auto-populate SQLite models!
    if trip_id:
        try:
            trip = Trip.objects.get(id=trip_id)
            if request.user.is_authenticated and trip.user == request.user:
                trip.itineraries.all().delete()
                for day_data in result.get('days', []):
                    day_num = day_data.get('day', 1)
                    itin_obj = Itinerary.objects.create(
                        trip=trip,
                        day_number=day_num,
                        date=trip.start_date + timedelta(days=day_num - 1),
                        title=day_data.get('theme', f'Day {day_num} Plan'),
                        city_name=day_data.get('city_name', destination.split(',')[0]),
                        notes=day_data.get('notes', ''),
                        allocated_budget=Decimal(str(day_data.get('allocated_budget', 0)))
                    )
                    for act in day_data.get('activities', []):
                        ItineraryItem.objects.create(
                            itinerary=itin_obj,
                            name=act.get('activity_name') or act.get('name', 'Activity'),
                            category=act.get('category', 'sightseeing'),
                            time=act.get('time', '09:00 AM'),
                            estimated_cost=Decimal(str(act.get('estimated_cost', 200))),
                            description=act.get('description', '')
                        )
                result['saved_to_trip'] = True
                result['trip_id'] = trip.id
        except Exception as e:
            result['save_error'] = str(e)

    return JsonResponse(result, safe=False)


@csrf_exempt
def smart_budget_api(request):
    """
    POST /ai/budget/
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST if request.method == 'POST' else request.GET

    destination = data.get('destination', '').strip()
    days = data.get('days', 3)

    if not destination:
        return JsonResponse({'error': 'destination parameter is required'}, status=400)

    try:
        days = int(days)
    except Exception:
        days = 3

    result = generate_smart_budget_rupees(destination, days=days)
    return JsonResponse(result, safe=False)


@csrf_exempt
def activity_recommendation_api(request):
    """
    POST /ai/activities/
    """
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'POST method required'}, status=405)

    if request.content_type == 'application/json' and request.body:
        try:
            data = json.loads(request.body)
        except Exception:
            data = {}
    else:
        data = request.POST if request.method == 'POST' else request.GET

    city = data.get('city') or data.get('destination', '').strip()
    if not city:
        return JsonResponse({'error': 'city parameter is required'}, status=400)

    acts = fetch_activities_for_city_ai(city)
    return JsonResponse({'city': city, 'activities': acts, 'currency': 'INR'}, safe=False)


def ai_tools_view(request):
    """
    Interactive web UI to test and interact with all 3 AI services with INR values.
    """
    user_trips = Trip.objects.filter(user=request.user) if request.user.is_authenticated else []
    return render(request, 'ai_services/ai_tools.html', {'user_trips': user_trips})