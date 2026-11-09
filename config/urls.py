
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

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

    # User Authentication and Profile Settings
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

    # Public About Us Page
    path(
        "about/",
        TemplateView.as_view(
            template_name="about.html"
        ),
        name="about",
    ),

    # Homepage
    path(
        "",
        home,
        name="home",
    ),

    # Weather, Earthquakes, Air Quality,
    # Groq AI and Saved Locations
    path(
        "",
        include("weather.urls"),
    ),
]
