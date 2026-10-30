
from django.contrib import admin
from django.urls import path, include

from weather.views import home
from dashboard.views import admin_dashboard_view


urlpatterns = [
    # Django Admin Panel
    path(
        "admin/",
        admin.site.urls,
    ),

    # Custom SkyAware PH Admin Dashboard
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

    # PayMongo Test Donations
    path(
        "",
        include("donations.urls"),
    ),

    # Homepage
    path(
        "",
        home,
        name="home",
    ),

    # Weather APIs and Saved Locations CRUD
    path(
        "",
        include("weather.urls"),
    ),
]
