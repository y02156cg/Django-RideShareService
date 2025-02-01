from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Driver


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin configuration for User model.
    Extends the default UserAdmin to include additional fields and methods.
    """
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_driver',
        'total_active_rides'
    )

    list_filter = (
        'is_staff',
        'is_active',
        'is_superuser',
        'groups'
    )

    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email'
    )

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    def is_driver(self, obj):
        """Check if the user is a driver."""
        return obj.is_driver()

    is_driver.boolean = True
    is_driver.short_description = 'Driver Status'

    def total_active_rides(self, obj):
        """Calculate total active rides for the user."""
        owned_rides = obj.get_owned_rides().count()
        shared_rides = obj.get_shared_rides().count()
        driven_rides = len(obj.get_driven_rides())
        return owned_rides + shared_rides + driven_rides

    total_active_rides.short_description = 'Active Rides'


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    """
    Admin configuration for Driver model.
    Provides detailed view and management of driver profiles.
    """
    list_display = (
        'get_full_name',
        'vehicle_type',
        'license_plate',
        'max_passengers',
        'get_total_driven_rides'
    )

    list_filter = (
        'vehicle_type',
        'max_passengers'
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'license_plate'
    )

    readonly_fields = (
        'get_username',
        'get_email'
    )

    fieldsets = (
        ('User Details', {
            'fields': (
                'get_username',
                'get_email',
                'get_full_name'
            )
        }),
        ('Vehicle Information', {
            'fields': (
                'license_plate',
                'vehicle_type',
                'max_passengers',
                'special_vehicle_info'
            )
        })
    )

    def get_full_name(self, obj):
        """Display full name of the driver."""
        return obj.user.get_full_name() or obj.user.username

    get_full_name.short_description = 'Full Name'

    def get_username(self, obj):
        """Return the associated user's username."""
        return obj.user.username

    get_username.short_description = 'Username'

    def get_email(self, obj):
        """Return the associated user's email."""
        return obj.user.email

    get_email.short_description = 'Email'

    def get_total_driven_rides(self, obj):
        """Calculate total driven rides."""
        return obj.driven_rides.count()

    get_total_driven_rides.short_description = 'Total Driven Rides'