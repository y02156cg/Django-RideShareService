from django.urls import path
from . import views

urlpatterns = [
    path('', views.RideListView.as_view(), name='ride_list'),
    path('create/', views.RideCreateView.as_view(), name='create_ride'),
    path('<int:pk>/', views.RideDetailView.as_view(), name='ride_detail'),
    path('<int:pk>/update/', views.RideUpdateView.as_view(), name='update_ride'),
    path('<int:pk>/complete/', views.RideCompleteView.as_view(), name='complete_ride'),
    path('<int:pk>/confirm/', views.RideConfirmView.as_view(), name='confirm_ride'),
    path('<int:pk>/join/', views.RideShareJoinView.as_view(), name='join_ride'),
    path('search/', views.ShareSearchView.as_view(), name='share_search'),
    path('driver/search/', views.DriverRideSearchView.as_view(), name='driver_search'),
]