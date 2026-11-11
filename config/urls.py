
from django.urls import path, include
from django.views.generic import TemplateView, RedirectView

from weather.views import home
from weather.natural_events import natural_events_view

from dashboard.views import admin_dashboard_view
from dashboard.admin_users import (
    admin_users_view,
    admin_user_detail_view,
)


# Compatibility for older templates using
# {% url 'admin:index' %}.
#
# This is NOT Django's built-in administration site.
# It redirects to our custom SkyAware PH Admin Dashboard.
legacy_admin_urls = (
    [
        path(
            "",
            RedirectView.as_view(
                pattern_name="admin_dashboard",
                permanent=False,
            ),
            name="index",
        ),
    ],
    "admin",
)


urlpatterns = [

    # Custom administrator overview
    path(
        "admin-dashboard/",
        admin_dashboard_view,
        name="admin_dashboard",
    ),

    # Custom administrator user management
    path(
        "admin-dashboard/users/",
        admin_users_view,
        name="admin_users",
    ),

    path(
        "admin-dashboard/users/<int:pk>/",
        admin_user_detail_view,
        name="admin_user_detail",
    ),

    # Legacy Django Admin links redirect
    # to the custom administration interface.
    path(
        "admin/",
        include(legacy_admin_urls, namespace="admin"),
    ),

    # Authentication and Profile Settings
    path(
        "accounts/",
        include("accounts.urls"),
    ),

    # Regular User Dashboard
    path(
        "dashboard/",
        include("dashboard.urls"),
    ),

    # NASA EONET Natural Events
    path(
        "natural-events/",
        natural_events_view,
        name="natural_events",
    ),

    # Public About Us Page
    path(
        "about/",
        TemplateView.as_view(
            template_name="about.html",
        ),
        name="about",
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
