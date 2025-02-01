from django import forms
from .models import Ride, RideShare
from django.utils import timezone
from account.models import Driver

class RideRequestForm(forms.ModelForm):
    class Meta:
        model = Ride
        fields = ['destination', 'arrival_time', 'passengers_count', 'vehicle_type', 'special_request', 'sharable']
        widgets = {'arrival_time': forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
            ),
            'special_request': forms.Textarea(
                attrs={
                    'rows': 3,
                    'placeholder': 'Enter any special requests that must match driver vehicle info'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.arrival_time:
            self.fields['arrival_time'].initial = self.instance.arrival_time.strftime('%Y-%m-%dT%H:%M')

    def clean_arrival_time(self):
        arrival_time = self.cleaned_data.get('arrival_time')
        if arrival_time and arrival_time < timezone.now():
            raise forms.ValidationError('Arrival time cannot be shorter than now.')
        return arrival_time

    def clean_passengers_count(self):
        passengers = self.cleaned_data.get('passengers_count')
        if passengers < 1:
            raise forms.ValidationError('Passengers number must be at least 1.')
        return passengers

class ShareSearchForm(forms.Form):
    destination = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Enter destination'})
    )
    earliest_arrival = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    latest_arrival = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    passengers = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'placeholder': 'Number of passengers'})
    )

    def clean(self):
        cleaned_data = super().clean()
        earliest = cleaned_data.get('earliest_arrival')
        latest = cleaned_data.get('latest_arrival')

        if earliest and latest:
            if earliest < timezone.now():
                raise forms.ValidationError('Earliest arrival time must be in the future.')
            if earliest >= latest:
                raise forms.ValidationError('Earliest arrival must be before latest arrival.')
        return cleaned_data

class RideShareJoinForm(forms.ModelForm):
    class Meta:
        model = RideShare
        fields = ['passengers', 'earliest_arrival', 'latest_arrival']
        widgets = {
            'earliest_arrival': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'latest_arrival': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            )
        }

    def __init__(self, *args, ride=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ride = ride

    def clean(self):
        cleaned_data = super().clean()
        if self.ride and not self.ride.can_be_shared():
            raise forms.ValidationError('This ride cannot be shared.')

        earliest = cleaned_data.get('earliest_arrival')
        latest = cleaned_data.get('latest_arrival')
        passengers = cleaned_data.get('passengers')

        if earliest and latest:
            if earliest < timezone.now():
                raise forms.ValidationError('Earliest arrival time must be in the future.')
            if earliest >= latest:
                raise forms.ValidationError('Earliest arrival must be before latest arrival.')
            if self.ride and not (earliest <= self.ride.arrival_time <= latest):
                raise forms.ValidationError('Ride arrival time is outside your acceptable window.')

        if self.ride and passengers:
            if not self.ride.can_passengers_count(passengers):
                raise forms.ValidationError('Ride cannot accommodate this many passengers.')

        return cleaned_data

class DriverRideSearchForm(forms.Form):
    destination = forms.CharField(required=False)
    earliest_departure = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )

    def __init__(self, *args, driver=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver

class RideCompleteForm(forms.ModelForm):
    class Meta:
        model = Ride
        fields = ['status']
        widgets = {
            'status': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].initial = 'COMPLETE'

    def clean_status(self):
        status = self.cleaned_data.get('status')
        if status != 'COMPLETE':
            raise forms.ValidationError('Invalid status transition.')
        if self.instance.status != 'CONFIRMED':
            raise forms.ValidationError('Only confirmed rides can be marked as complete.')
        return status

class RideSearchForm(forms.Form):
    destination = forms.CharField(max_length=200)
    earliest_arrival = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    latest_arrival = forms.DateTimeField(
        widget=forms.DateTimeInput(
            attrs={'type': 'datetime-local'},
            format='%Y-%m-%dT%H:%M'
        )
    )
    passengers_count = forms.IntegerField(min_value=1)

    def clean(self):
        cleaned_data = super().clean()
        earliest = cleaned_data.get('earliest_arrival')
        latest = cleaned_data.get('latest_arrival')

        if earliest and latest:
            if earliest >= latest:
                raise forms.ValidationError('Earliest arrival must be before latest arrival.')
        return cleaned_data

class RideShareForm(forms.ModelForm):
    class Meta:
        model = RideShare
        fields = ['passengers', 'earliest_arrival', 'latest_arrival']
        widgets = {
            'earliest_arrival': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'latest_arrival': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            )
        }