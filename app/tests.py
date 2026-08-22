import json
from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Trip, TripStop, Itinerary, ItineraryItem, City

User = get_user_model()

class AppTripAndAiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='dev_coderji',
            email='coderji@example.com',
            password='Password123!',
            first_name='Technical',
            last_name='Coderji'
        )
        self.client.login(username='dev_coderji', password='Password123!')

        self.start = timezone.now().date() + timedelta(days=5)
        self.end = self.start + timedelta(days=3)

        self.trip = Trip.objects.create(
            user=self.user,
            name='Gujarat Coastal Pilgrimage',
            description='Dwarka and Somnath sacred tour',
            start_date=self.start,
            end_date=self.end,
            estimated_budget=Decimal('18000.00'),
            is_public=True
        )
        TripStop.objects.create(trip=self.trip, city_name='Dwarka, Gujarat', order=1)
        TripStop.objects.create(trip=self.trip, city_name='Somnath, Gujarat', order=2)

    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Gujarat Coastal Pilgrimage')

    def test_multi_city_planning_flow(self):
        # Step 1: Save dates & add destination
        resp1 = self.client.post(reverse('start_trip'), {
            'action': 'save_dates',
            'name': 'Rajasthan Heritage Tour',
            'start_date': str(self.start),
            'end_date': str(self.end),
            'budget': '20000',
            'description': 'Jaipur & Udaipur exploration'
        })
        self.assertEqual(resp1.status_code, 302)

        # Add cities
        self.client.post(reverse('start_trip'), {'action': 'add_city', 'city_name': 'Jaipur, Rajasthan'})
        self.client.post(reverse('start_trip'), {'action': 'add_city', 'city_name': 'Udaipur, Rajasthan'})

        # Step 2: Pick activities for Jaipur
        resp2 = self.client.post(reverse('step2_events'), {
            'selected_events': ['Amber Fort Heritage Walk', 'Hawa Mahal Photography']
        })
        self.assertEqual(resp2.status_code, 302)

        # Pick activities for Udaipur
        resp3 = self.client.post(reverse('step2_events'), {
            'selected_events': ['City Palace Udaipur', 'Lake Pichola Boat Ride']
        })
        self.assertEqual(resp3.status_code, 302)

        # Step 3: Finalize Plan
        resp_final = self.client.get(reverse('step3_final_plan'))
        self.assertEqual(resp_final.status_code, 302)

        new_trip = Trip.objects.filter(name='Rajasthan Heritage Tour').first()
        self.assertIsNotNone(new_trip)
        self.assertEqual(new_trip.stops.count(), 2)
        self.assertTrue(new_trip.itineraries.count() > 0)

    def test_itinerary_builder_and_add_item(self):
        day = Itinerary.objects.create(
            trip=self.trip,
            day_number=1,
            title='Dwarka Temples',
            city_name='Dwarka',
            allocated_budget=Decimal('6000.00')
        )
        response = self.client.get(reverse('itinerary_builder', kwargs={'trip_id': self.trip.id}))
        self.assertEqual(response.status_code, 200)

        # Add item to day
        add_item_resp = self.client.post(reverse('add_item', kwargs={'trip_id': self.trip.id, 'day_id': day.id}), {
            'name': 'Dwarkadhish Temple Mangla Aarti',
            'category': 'culture',
            'time': '06:30 AM',
            'estimated_cost': '150.00',
            'description': 'Early morning divine darshan'
        })
        self.assertEqual(add_item_resp.status_code, 302)
        self.assertEqual(day.items.count(), 1)
        self.assertEqual(self.trip.total_cost, Decimal('150.00'))

    def test_budget_view_inr(self):
        day = Itinerary.objects.create(trip=self.trip, day_number=1, title='Day 1', allocated_budget=Decimal('5000.00'))
        ItineraryItem.objects.create(itinerary=day, name='Temple Darshan', estimated_cost=Decimal('200.00'))

        response = self.client.get(reverse('trip_budget', kwargs={'trip_id': self.trip.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '200.00')

    def test_calendar_view(self):
        Itinerary.objects.create(trip=self.trip, day_number=1, title='Day 1', date=self.start)
        response = self.client.get(reverse('trip_calendar', kwargs={'trip_id': self.trip.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Schedule Timeline')

    def test_export_json_and_copy_trip(self):
        # JSON export
        resp_json = self.client.get(reverse('trip_export_json', kwargs={'trip_id': self.trip.id}))
        self.assertEqual(resp_json.status_code, 200)
        self.assertEqual(resp_json['Content-Type'], 'application/json')

        # Copy trip
        other_user = User.objects.create_user(username='other_traveler', password='Password123!')
        self.client.login(username='other_traveler', password='Password123!')
        resp_copy = self.client.get(reverse('trip_copy', kwargs={'trip_id': self.trip.id}))
        self.assertEqual(resp_copy.status_code, 302)
        self.assertTrue(Trip.objects.filter(user=other_user, name__startswith='Copy of').exists())

    def test_ai_generate_itinerary_endpoint(self):
        payload = {
            'destination': 'Dwarka & Somnath',
            'number_of_days': 3,
            'budget': 12000
        }
        resp = self.client.post(
            reverse('ai_generate_itinerary'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('days', data)
        self.assertEqual(data.get('currency'), 'INR')

    def test_ai_budget_endpoint_inr(self):
        payload = {'destination': 'Dwarka', 'days': 3}
        resp = self.client.post(
            reverse('ai_smart_budget'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('estimated_total_budget', data)
        self.assertEqual(data.get('currency'), 'INR')

    def test_ai_activities_endpoint(self):
        payload = {'city': 'Dwarka'}
        resp = self.client.post(
            reverse('ai_activities'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('activities', data)
        self.assertTrue(len(data['activities']) > 0)
