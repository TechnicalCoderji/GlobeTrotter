from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

class City(models.Model):
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="India")
    cost_index = models.CharField(max_length=50, default="Medium", choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')])
    popularity = models.IntegerField(default=50)

    class Meta:
        verbose_name_plural = "Cities"
        ordering = ['name']

    def __str__(self):
        return f"{self.name}, {self.country}"


class Trip(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trips')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=15000.00, help_text="Total estimated budget in ₹ Rupees")
    is_public = models.BooleanField(default=False, help_text="Share publicly with the GlobeTrotter community")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    @property
    def title(self):
        return self.name

    @property
    def budget(self):
        return self.estimated_budget

    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            return max(delta, 1)
        return 1

    @property
    def status(self):
        today = timezone.now().date()
        if self.start_date > today:
            return "Upcoming"
        elif self.start_date <= today <= self.end_date:
            return "Ongoing"
        else:
            return "Completed"

    @property
    def total_cost(self):
        total = Decimal('0.00')
        for itin in self.itineraries.all():
            for item in itin.items.all():
                total += item.estimated_cost
        return total

    @property
    def total_activities(self):
        count = 0
        for itin in self.itineraries.all():
            count += itin.items.count()
        return count

    @property
    def is_overbudget(self):
        return self.total_cost > self.estimated_budget if self.estimated_budget > 0 else False

    @property
    def budget_progress_percentage(self):
        if self.estimated_budget <= 0:
            return 0
        pct = (float(self.total_cost) / float(self.estimated_budget)) * 100
        return min(round(pct, 1), 100)

    @property
    def destination_display(self):
        stops = list(self.stops.values_list('city_name', flat=True))
        if stops:
            return ", ".join(stops)
        # Check itinerary city names
        itin_cities = [i.city_name for i in self.itineraries.all() if i.city_name]
        if itin_cities:
            return ", ".join(dict.fromkeys(itin_cities))
        return "Personalized Journey"


class TripStop(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='stops')
    city_name = models.CharField(max_length=150)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.city_name} (Stop {self.order} of {self.trip.name})"


class Itinerary(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itineraries')
    day_number = models.PositiveIntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    city_name = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    allocated_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['day_number']
        unique_together = ['trip', 'day_number']

    def __str__(self):
        return f"Day {self.day_number}: {self.title or self.trip.name}"

    @property
    def day_cost(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.estimated_cost
        return total


class ItineraryItem(models.Model):
    CATEGORY_CHOICES = [
        ('sightseeing', 'Sightseeing & Landmarks'),
        ('food', 'Food & Dining'),
        ('adventure', 'Adventure & Outdoors'),
        ('culture', 'Culture & Temple/History'),
        ('relaxation', 'Relaxation & Leisure'),
    ]

    itinerary = models.ForeignKey(Itinerary, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=250)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='sightseeing')
    time = models.CharField(max_length=50, default="09:00 AM")
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Cost in ₹ Rupees")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} at {self.time} (₹{self.estimated_cost})"

    @property
    def display_title(self):
        return self.name

    @property
    def display_category(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category.title())