
from decimal import Decimal

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from weather.models import SavedLocation
from donations.models import Donation


# ==========================================
# REGULAR USER DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):
    return render(
        request,
        "dashboard/index.html"
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@staff_member_required(login_url="login")
def admin_dashboard_view(request):

    User = get_user_model()

    # ======================================
    # USER STATISTICS
    # ======================================

    total_users = User.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    admin_users = User.objects.filter(
        is_staff=True
    ).count()

    total_saved_locations = (
        SavedLocation.objects.count()
    )

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:5]

    # ======================================
    # DONATION STATISTICS
    # ======================================

    total_donations = Donation.objects.count()

    successful_donations = Donation.objects.filter(
        status=Donation.Status.PAID
    ).count()

    pending_donations = Donation.objects.filter(
        status=Donation.Status.PENDING
    ).count()

    failed_donations = Donation.objects.filter(
        status=Donation.Status.FAILED
    ).count()

    cancelled_donations = Donation.objects.filter(
        status=Donation.Status.CANCELLED
    ).count()

    paid_amount = Donation.objects.filter(
        status=Donation.Status.PAID
    ).aggregate(
        total=Sum("amount")
    )["total"]

    total_donation_amount = (
        paid_amount
        if paid_amount is not None
        else Decimal("0.00")
    )

    recent_donations = (
        Donation.objects
        .select_related("user")
        .order_by("-created_at")[:5]
    )

    # ======================================
    # PAYMONGO CONFIGURATION
    # ======================================

    paymongo_key = getattr(
        settings,
        "PAYMONGO_SECRET_KEY",
        ""
    )

    paymongo_configured = (
        isinstance(paymongo_key, str)
        and paymongo_key.startswith("sk_test_")
        and len(paymongo_key) > len("sk_test_")
    )

    if paymongo_configured:
        paymongo_status = "Configured"
    else:
        paymongo_status = "Not Configured"

    # ======================================
    # API INTEGRATIONS
    # ======================================

    api_integrations = [
        {
            "name": "Open-Meteo Weather",
            "status": "Integrated"
        },
        {
            "name": "Open-Meteo Geocoding",
            "status": "Integrated"
        },
        {
            "name": "Open-Meteo Air Quality",
            "status": "Integrated"
        },
        {
            "name": "USGS Earthquake",
            "status": "Integrated"
        },
        {
            "name": "Groq AI Assistant",
            "status": "Integrated"
        },
        {
            "name": "PayMongo Test Checkout",
            "status": paymongo_status
        },
    ]

    # ======================================
    # DASHBOARD CONTEXT
    # ======================================

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "total_saved_locations": total_saved_locations,
        "recent_users": recent_users,

        "total_donations": total_donations,
        "successful_donations": successful_donations,
        "pending_donations": pending_donations,
        "failed_donations": failed_donations,
        "cancelled_donations": cancelled_donations,
        "total_donation_amount": total_donation_amount,
        "recent_donations": recent_donations,

        "paymongo_configured": paymongo_configured,
        "api_integrations": api_integrations,
    }

    return render(
        request,
        "dashboard/admin_dashboard.html",
        context
    )
