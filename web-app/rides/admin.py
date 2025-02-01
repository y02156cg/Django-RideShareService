from django.contrib import admin
from django.utils.html import format_html
from .models import Ride, RideShare


@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    """Admin configuration for Ride model."""
    list_display = (
        'id',
        'owner_name',
        'destination',
        'arrival_time',
        'passengers_count',
        'total_passengers',
        'status',
        'driver_name',
        'sharable',
        'created_at'
    )

    list_filter = (
        'status',
        'sharable',
        'vehicle_type',
        'created_at',
        'arrival_time'
    )

    search_fields = (
        'owner__username',
        'owner__email',
        'destination',
        'driver__name',
        'special_request'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'total_passengers'
    )

    fieldsets = (
        ('Ride Details', {
            'fields': (
                'owner',
                'destination',
                'arrival_time',
                'passengers_count',
                'vehicle_type',
                'special_request'
            )
        }),
        ('Ride Status', {
            'fields': (
                'status',
                'driver',
                'sharable'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            )
        })
    )

    def owner_name(self, obj):
        """Display owner's full name or username."""
        return obj.owner.get_full_name() or obj.owner.username

    owner_name.short_description = 'Owner'

    def driver_name(self, obj):
        """Display driver's name if assigned."""
        return obj.driver.name if obj.driver else 'Unassigned'

    driver_name.short_description = 'Driver'


@admin.register(RideShare)
class RideShareAdmin(admin.ModelAdmin):
    """Admin configuration for RideShare model."""
    list_display = (
        'id',
        'ride_details',
        'sharer_name',
        'passengers',
        'arrival_window',
        'joined_at'
    )

    list_filter = (
        'passengers',
        'joined_at'
    )

    search_fields = (
        'sharer__username',
        'sharer__email',
        'ride__destination'
    )

    readonly_fields = (
        'joined_at',
    )

    def sharer_name(self, obj):
        """Display sharer's full name or username."""
        return obj.sharer.get_full_name() or obj.sharer.username

    sharer_name.short_description = 'Sharer'

    def ride_details(self, obj):
        """Display ride destination and status."""
        return f"{obj.ride.destination} ({obj.ride.status})"

    ride_details.short_description = 'Ride'

    def arrival_window(self, obj):
        """Display arrival window as a formatted string."""
        return format_html(
            '{} - {}',
            obj.earliest_arrival.strftime('%Y-%m-%d %H:%M'),
            obj.latest_arrival.strftime('%Y-%m-%d %H:%M')
        )

    arrival_window.short_description = 'Arrival Window'