
from django.urls import path
from . import views


urlpatterns = [

    # Weather Forecast
    path(
        'forecast/',
        views.weather_forecast,
        name='weather_forecast'
    ),

    # Earthquake Updates
    path(
        'earthquakes/',
        views.earthquake_updates,
        name='earthquake_updates'
    ),

    # Saved Locations - Read
    path(
        'locations/',
        views.saved_locations,
        name='saved_locations'
    ),

    # Saved Locations - Create
    path(
        'locations/add/',
        views.add_location,
        name='add_location'
    ),

    # Saved Locations - Update
    path(
        'locations/<int:pk>/edit/',
        views.edit_location,
        name='edit_location'
    ),

    # Saved Locations - Delete
    path(
        'locations/<int:pk>/delete/',
        views.delete_location,
        name='delete_location'
    ),
]
