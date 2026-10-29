
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from weather.models import SavedLocation


# ==========================================
# REGULAR USER DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    return render(request, "dashboard/index.html")


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@staff_member_required(login_url="login")
def admin_dashboard_view(request):

    User = get_user_model()

    total_users = User.objects.count()

    total_saved_locations = SavedLocation.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    admin_users = User.objects.filter(
        is_staff=True
    ).count()

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:5]

    api_integrations = [
        {
            "name": "Open-Meteo Weather",
            "status": "Integrated"
        },
        {
            "name": "USGS Earthquake",
            "status": "Integrated"
        },
        {
            "name": "Open-Meteo Air Quality",
            "status": "Integrated"
        },
        {
            "name": "Groq AI Assistant",
            "status": "Integrated"
        }
    ]

    context = {
        "total_users": total_users,
        "total_saved_locations": total_saved_locations,
        "active_users": active_users,
        "admin_users": admin_users,
        "recent_users": recent_users,
        "api_integrations": api_integrations,
    }

    return render(
        request,
        "dashboard/admin_dashboard.html",
        context
    )
