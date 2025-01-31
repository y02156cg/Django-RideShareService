from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from account.models import Driver


class Ride(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CONFIRMED', 'Confirmed'),
        ('COMPLETE', 'Complete'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_rides'
    )
    driver = models.ForeignKey(
        'account.Driver',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='driven_rides'
    )

    destination = models.CharField(max_length=255)
    arrival_time = models.DateTimeField()
    passengers_count = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of passengers in owner's party",
        default=1
    )
    vehicle_type = models.CharField(max_length=10, choices=Driver.VEHICLE_TYPES, blank=True, null=True)
    special_request = models.TextField(blank=True, null=True)
    sharable = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_passengers(self):
        sharer_passengers = self.ride_shares.aggregate(total=models.Sum('passengers'))['total'] or 0
        if hasattr(self, '_passengers_count'):
            passengers_count = self.passengers_count
        else:
            passengers_count = 0
        return passengers_count + sharer_passengers

    def can_be_edited(self) -> bool:
        return self.status == 'OPEN'

    def can_be_shared(self) -> bool:
        return self.status == 'OPEN' and self.sharable

    def confirm_with_driver(self, driver: Driver) -> bool:
        if self.status != 'OPEN' or not driver.is_eligible_for_ride(self):
            return False
        self.driver = driver
        self.status = 'CONFIRMED'
        self.save()
        return True

    def can_passengers_count(self, additional_passengers: int) -> bool:
        if not self.can_be_shared():
            return False

        if self.driver:
            total_after_adding = self.total_passengers + additional_passengers
            return total_after_adding <= self.driver.max_passengers

        return True

    def mark_complete(self) -> bool:
        if self.status != 'CONFIRMED':
            return False
        self.status = 'COMPLETE'
        self.save()
        return True

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['destination']),
            models.Index(fields=['arrival_time']),
        ]
        ordering = ['-arrival_time']


class RideShare(models.Model):
    """
    Represents a sharer joining an existing ride.
    """
    ride = models.ForeignKey(
        Ride,
        on_delete=models.CASCADE,
        related_name='ride_shares'
    )
    sharer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rideshare_set'
    )
    passengers = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Number of passengers in sharer's party"
    )
    earliest_arrival = models.DateTimeField()
    latest_arrival = models.DateTimeField()
    joined_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()

        if self.earliest_arrival >= self.latest_arrival:
            raise models.ValidationError({
                'earliest_arrival': 'Must be before latest arrival time'
            })

        if not (self.earliest_arrival <= self.ride.arrival_time <= self.latest_arrival):
            raise models.ValidationError(
                'Ride arrival time is outside acceptable window'
            )

        if not self.ride.can_be_shared():
            raise models.ValidationError('This ride cannot be shared')

        if not self.ride.can_passengers_count(self.passengers):
            raise models.ValidationError(
                'Exceed maximum passenger number'
            )

    def __str__(self):
        return f"{self.sharer.get_full_name()} - {self.passengers} passenger(s)"

    class Meta:
        unique_together = ['ride', 'sharer']  # Prevent duplicate shares
        indexes = [
            models.Index(fields=['ride', 'sharer']),
        ]
        ordering = ['joined_at']