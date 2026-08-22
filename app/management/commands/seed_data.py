from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from app.models import Trip, TripStop, Itinerary, ItineraryItem, City

User = get_user_model()

class Command(BaseCommand):
    help = "Seeds initial demo user and personalized trips in Rupees"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding GlobeTrotter database..."))

        # 1. Create Demo User
        demo_user, created = User.objects.get_or_create(
            username="technicalcoderji",
            defaults={
                'first_name': "Technical",
                'last_name': "Coderji",
                'email': "coderji@globetrotter.io",
                'city': "Ahmedabad",
                'country': "India",
                'bio': "Passionate traveler, spiritual explorer, and developer.",
            }
        )
        if created:
            demo_user.set_password("Coderji123!")
            demo_user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: technicalcoderji (pwd: Coderji123!)"))

        # 2. Create Sample Personalized Trip: Dwarka & Somnath
        start_d = timezone.now().date() + timedelta(days=7)
        end_d = start_d + timedelta(days=3)

        trip1, t1_created = Trip.objects.get_or_create(
            user=demo_user,
            name="Divine Coastal Saurashtra: Dwarka & Somnath",
            defaults={
                'description': "A 4-day pilgrimage and coastal tour covering Dwarkadhish Temple, Bet Dwarka, Nageshwar, and Somnath Jyotirlinga.",
                'start_date': start_d,
                'end_date': end_d,
                'estimated_budget': Decimal('16000.00'),
                'is_public': True
            }
        )

        if t1_created:
            TripStop.objects.create(trip=trip1, city_name="Dwarka, Gujarat", order=1)
            TripStop.objects.create(trip=trip1, city_name="Somnath, Gujarat", order=2)

            # Day 1: Dwarka
            d1 = Itinerary.objects.create(
                trip=trip1,
                day_number=1,
                date=start_d,
                city_name="Dwarka",
                title="Dwarka Arrival & Sacred Jagat Mandir Darshan",
                notes="Morning Mangla Aarti at Dwarkadhish temple followed by Gomti Ghat walk.",
                allocated_budget=Decimal('4000.00')
            )
            ItineraryItem.objects.create(itinerary=d1, name="Dwarkadhish Temple Mangla Darshan", category="culture", time="06:30 AM", estimated_cost=Decimal('150.00'), description="Sacred darshan at the 5-story ancient temple.")
            ItineraryItem.objects.create(itinerary=d1, name="Authentic Gujarati Thali Lunch", category="food", time="01:00 PM", estimated_cost=Decimal('250.00'), description="Traditional unlimited kathiyawadi lunch with buttermilk.")
            ItineraryItem.objects.create(itinerary=d1, name="Gomti Ghat Sunset & Evening Aarti", category="sightseeing", time="06:30 PM", estimated_cost=Decimal('50.00'), description="Sunset where Gomti river meets the Arabian Sea.")

            # Day 2: Bet Dwarka & Nageshwar
            d2 = Itinerary.objects.create(
                trip=trip1,
                day_number=2,
                date=start_d + timedelta(days=1),
                city_name="Dwarka",
                title="Bet Dwarka Island & Nageshwar Jyotirlinga",
                notes="Ferry ride from Okha port to Bet Dwarka.",
                allocated_budget=Decimal('4000.00')
            )
            ItineraryItem.objects.create(itinerary=d2, name="Bet Dwarka Ferry Boat Ride & Mandir", category="adventure", time="08:30 AM", estimated_cost=Decimal('300.00'), description="Scenic boat crossing in Gulf of Kutch to the historic island.")
            ItineraryItem.objects.create(itinerary=d2, name="Nageshwar Jyotirlinga Temple Visit", category="culture", time="02:30 PM", estimated_cost=Decimal('100.00'), description="One of the 12 sacred Jyotirlinga shrines.")
            ItineraryItem.objects.create(itinerary=d2, name="Shivrajpur Blue Flag Beach Walk", category="relaxation", time="05:30 PM", estimated_cost=Decimal('200.00'), description="Pristine white sand certified Blue Flag beach.")

            # Day 3: Somnath
            d3 = Itinerary.objects.create(
                trip=trip1,
                day_number=3,
                date=start_d + timedelta(days=2),
                city_name="Somnath",
                title="Transfer to Somnath & First Jyotirlinga Darshan",
                notes="Scenic coastal highway drive from Dwarka to Somnath.",
                allocated_budget=Decimal('4000.00')
            )
            ItineraryItem.objects.create(itinerary=d3, name="Somnath Temple Afternoon Darshan", category="culture", time="03:00 PM", estimated_cost=Decimal('150.00'), description="Majestic seaside temple honoring the first of twelve Jyotirlingas.")
            ItineraryItem.objects.create(itinerary=d3, name="Somnath Light & Sound Show at Sea Promenade", category="sightseeing", time="07:30 PM", estimated_cost=Decimal('100.00'), description="Laser and audio presentation on temple history by the sea.")

            # Day 4: Triveni Sangam & Bhalka Tirth
            d4 = Itinerary.objects.create(
                trip=trip1,
                day_number=4,
                date=start_d + timedelta(days=3),
                city_name="Somnath",
                title="Triveni Sangam & Sacred Sites",
                notes="Morning holy dip and temple darshans.",
                allocated_budget=Decimal('4000.00')
            )
            ItineraryItem.objects.create(itinerary=d4, name="Triveni Sangam Holy Dip & Boat Ride", category="adventure", time="08:00 AM", estimated_cost=Decimal('200.00'), description="Confluence of three holy rivers: Hiran, Kapila, and Saraswati.")
            ItineraryItem.objects.create(itinerary=d4, name="Bhalka Tirth Sacred Visit", category="culture", time="11:30 AM", estimated_cost=Decimal('80.00'), description="Spot where Lord Krishna concluded his earthly avatar.")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully! Ready for immediate use."))
