from django import  forms
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import MinValueValidator
from .models import User, Driver

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

class DriverRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        help_text="Driver's first name"
    )
    last_name = forms.CharField(
        required=True,
        help_text="Driver's last name"
    )

    class Meta:
        model = Driver
        fields = ['first_name', 'last_name', 'license_plate', 'vehicle_type',
                  'max_passengers', 'special_vehicle_info']
        widgets = {
            'special_vehicle_info': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Enter any special vehicle information'}
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user'):  # Check if user exists
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        driver = super().save(commit=False)

        # Only enforce user check if user was already assigned
        if commit and (not hasattr(driver, 'user') or driver.user is None):
            raise ValueError("User must be assigned before saving Driver instance.")

        # Assign user details before saving
        if hasattr(driver, 'user') and driver.user:
            driver.user.first_name = self.cleaned_data['first_name']
            driver.user.last_name = self.cleaned_data['last_name']
            driver.user.save()

        if commit:
            driver.save()
        return driver

    def clean_max_passengers(self):
        max_passengers = self.cleaned_data.get('max_passengers')
        if max_passengers < 1:
            raise forms.ValidationError('Maximum passengers must be at least 1.')
        return max_passengers

    def clean_license_plate(self):
        license_plate = self.cleaned_data.get('license_plate')
        if Driver.objects.filter(license_plate=license_plate).exists():
            if not self.instance or self.instance.license_plate != license_plate:
                raise forms.ValidationError(
                    'This license plate is already registered.'
                )
        return license_plate

class DriverProfileUpdateForm(DriverRegisterForm):
    class Meta(DriverRegisterForm.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
