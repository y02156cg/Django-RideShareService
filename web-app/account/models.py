from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db.models.query import QuerySet

class User(AbstractUser):
    email = models.EmailField(unique=True)

    def is_driver(self):
        return hasattr(self, 'driver_profile')

    def get_owned_rides(self):
        return self.owned_rides.exclude(status='complete')

    def get_shared_rides(self):
        return self.rideshare_set.exclude(ride__status='complete').select_related('ride')

    def get_driven_rides(self):
        if self.is_driver():
            return self.driver_profile.driven_rides.exclude(status='complete')
        return []

    def __str__(self):
        return self.username

class Driver(models.Model):
    VEHICLE_TYPES = [
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('van', 'Van'),
        ('luxury', 'Luxury'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )

    license_plate = models.CharField(max_length=20, unique=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    max_passengers = models.IntegerField(validators=[MinValueValidator(1)])
    special_vehicle_info = models.TextField(
        blank=True,
    )

    driven_rides: QuerySet = None

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['vehicle_type']),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vehicle_type}"

    def is_eligible_for_ride(self, ride):
        if ride.total_passengers > self.max_passengers:
            return False

        if ride.vehicle_type and ride.vehicle_type != self.vehicle_type:
            return False

        if (ride.special_request and self.special_vehicle_info and
                ride.special_request != self.special_vehicle_info):
            return False

        return True


