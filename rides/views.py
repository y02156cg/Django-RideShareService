from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Ride, RideShare
from .forms import (RideRequestForm, ShareSearchForm, RideShareJoinForm,
                    DriverRideSearchForm, RideCompleteForm)


class RideListView(LoginRequiredMixin, ListView):
    model = Ride
    template_name = 'rides/ride_list.html'
    context_object_name = 'rides'

    def get_queryset(self):
        user = self.request.user
        return Ride.objects.filter(
            Q(owner=user) |
            Q(ride_shares__sharer=user) |
            Q(driver__user=user)
        ).exclude(status='COMPLETE').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        rides = context['rides']

        for ride in rides:
            ride.user_role = 'owner' if ride.owner == user else (
                'driver' if ride.driver and ride.driver.user == user else 'sharer'
            )
        return context


class RideCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new ride request"""
    model = Ride
    form_class = RideRequestForm
    template_name = 'rides/create_ride.html'
    success_url = reverse_lazy('ride_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Ride request created successfully!')
        return response


class RideUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating a ride request"""
    model = Ride
    form_class = RideRequestForm
    template_name = 'rides/update_ride.html'
    success_url = reverse_lazy('ride_list')

    def test_func(self):
        ride = self.get_object()
        return ride.owner == self.request.user and ride.can_be_edited()

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Ride updated successfully!')
        return response


class ShareSearchView(LoginRequiredMixin, ListView):
    """View for searching sharable rides"""
    model = Ride
    template_name = 'rides/share_search.html'
    context_object_name = 'available_rides'
    form_class = ShareSearchForm

    def get_queryset(self):
        form = self.form_class(self.request.GET)
        if form.is_valid():
            destination = form.cleaned_data['destination']
            earliest = form.cleaned_data['earliest_arrival']
            latest = form.cleaned_data['latest_arrival']
            passengers = form.cleaned_data['passengers']

            return Ride.objects.filter(
                status='OPEN',
                sharable=True,
                destination__icontains=destination,
                arrival_time__range=(earliest, latest)
            ).exclude(owner=self.request.user)
        return Ride.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(self.request.GET or None)
        return context


class RideShareJoinView(LoginRequiredMixin, CreateView):
    """View for joining a shared ride"""
    model = RideShare
    form_class = RideShareJoinForm
    template_name = 'rides/join_ride.html'
    success_url = reverse_lazy('ride_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ride'] = get_object_or_404(Ride, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        form.instance.ride = get_object_or_404(Ride, pk=self.kwargs['pk'])
        form.instance.sharer = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, 'Successfully joined the ride!')
        return response


class DriverRideSearchView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View for drivers to search rides"""
    model = Ride
    template_name = 'rides/driver_search.html'
    context_object_name = 'available_rides'
    form_class = DriverRideSearchForm

    def test_func(self):
        return hasattr(self.request.user, 'driver_profile')

    def get_queryset(self):
        user = self.request.user
        if not user.is_driver():
            return Ride.objects.none()

        rides = Ride.objects.filter(status='OPEN')
        if self.request.GET:
            form = self.form_class(self.request.GET, driver=user.driver_profile)
            if form.is_valid():
                destination = form.cleaned_data.get('destination')
                if destination:
                    rides = rides.filter(destination__icontains=destination)

        return [ride for ride in rides if user.driver_profile.is_eligible_for_ride(ride)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(
            self.request.GET or None,
            driver=self.request.user.driver_profile
        )
        return context


class RideConfirmView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for drivers to confirm rides"""
    model = Ride
    fields = []  # No fields needed as we're just confirming
    template_name = 'rides/confirm_ride.html'
    success_url = reverse_lazy('ride_list')

    def test_func(self):
        return hasattr(self.request.user, 'driver_profile')

    def post(self, request, *args, **kwargs):
        ride = self.get_object()
        if ride.confirm_with_driver(request.user.driver_profile):
            messages.success(request, 'Ride confirmed successfully!')
            # Send confirmation emails
            subject = 'Ride Confirmation'
            message = f'Your ride to {ride.destination} has been confirmed.'
            recipients = [ride.owner.email]
            recipients.extend([share.sharer.email for share in ride.ride_shares.all()])
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients)
        else:
            messages.error(request, 'Unable to confirm ride.')
        return redirect(self.success_url)


class RideDetailView(LoginRequiredMixin, DetailView):
    """View for showing detailed information about a specific ride"""
    model = Ride
    template_name = 'rides/ride_detail.html'
    context_object_name = 'ride'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        ride = self.object

        # Add user roles to context
        context['is_owner'] = ride.owner == user
        context['is_sharer'] = ride.ride_shares.filter(sharer=user).exists()
        context['is_driver'] = hasattr(user, 'driver_profile') and ride.driver and ride.driver.user == user

        # Get all sharers info
        context['ride_shares'] = ride.ride_shares.select_related('sharer').all()

        return context


class RideCompleteView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for drivers to mark rides as complete"""
    model = Ride
    form_class = RideCompleteForm
    template_name = 'rides/complete_ride.html'
    success_url = reverse_lazy('ride_list')

    def test_func(self):
        ride = self.get_object()
        return (hasattr(self.request.user, 'driver_profile') and
                ride.driver and ride.driver.user == self.request.user)

    def form_valid(self, form):
        if self.object.mark_complete():
            messages.success(self.request, 'Ride marked as complete!')
            return redirect(self.success_url)
        messages.error(self.request, 'Unable to complete ride.')
        return redirect('ride_detail', pk=self.object.pk)