
from django.contrib import admin
from django.urls import path, include

from weather.views import home
from weather.natural_events import natural_events_view
from dashboard.views import admin_dashboard_view


urlpatterns = [

    # Django Admin
    path(
        "admin/",
        admin.site.urls,
    ),

    # SkyAware Admin Dashboard
    path(
        "admin-dashboard/",
        admin_dashboard_view,
        name="admin_dashboard",
    ),

    # Authentication
    path(
        "accounts/",
        include("accounts.urls"),
    ),

    # User Dashboard
    path(
        "dashboard/",
        include("dashboard.urls"),
    ),

    # NASA Natural Events
    path(
        "natural-events/",
        natural_events_view,
        name="natural_events",
    ),

    # Homepage
    path(
        "",
        home,
        name="home",
    ),

    # Weather, Air Quality, Earthquakes,
    # Groq AI and Saved Locations
    path(
        "",
        include("weather.urls"),
    ),

]
