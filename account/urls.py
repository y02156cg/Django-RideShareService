from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('login/', views.CustomLoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('driver/register', views.DriverRegisterView.as_view(), name='driver_register'),
    path('driver/profile/', views.DriverProfileUpdateView.as_view(), name='driver_profile'),
]