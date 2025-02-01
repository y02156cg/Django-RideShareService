from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Driver
from .forms import UserRegisterForm, DriverRegisterForm, DriverProfileUpdateForm

class UserRegisterView(CreateView):
    form_class = UserRegisterForm
    template_name = 'account/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Account registration successfully.')
        return response

class CustomLoginView(LoginView):
    template_name = 'account/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('ride_list')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

class DriverRegisterView(LoginRequiredMixin, CreateView):
    form_class = DriverRegisterForm
    template_name = 'account/driver_register.html'
    success_url = reverse_lazy('driver_profile')

    def form_valid(self, form):
        driver = form.save(commit=False)  # Create instance but don't save yet
        driver.user = self.request.user  # Assign the logged-in user
        driver.save()  # Now it's safe to save

        messages.success(self.request, 'Successfully registered as a driver!')
        return redirect(self.success_url)  # Redirect to driver's profile page



class DriverProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverProfileUpdateForm
    template_name = 'account/driver_update.html'
    success_url = reverse_lazy('driver_profile')

    def get_object(self, queryset=None):
        return Driver.objects.get(user=self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Driver profile updated successfully.')
        return response
