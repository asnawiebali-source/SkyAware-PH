
"""SkyAware PH user and admin dashboards."""

from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import hashlib

import requests
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from weather.models import SavedLocation
from donations.models import Donation


def _weather_condition(code):
    if code is None:
        return ("Conditions unavailable", "bi-cloud")
    if code == 0:
        return ("Clear sky", "bi-sun")
    if code in (1, 2):
        return ("Partly cloudy", "bi-cloud-sun")
    if code == 3:
        return ("Cloudy", "bi-clouds")
    if code in (45, 48):
        return ("Foggy", "bi-cloud-fog")
    if code in (51, 53, 55, 56, 57):
        return ("Drizzle", "bi-cloud-drizzle")
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return ("Rainy", "bi-cloud-rain")
    if code in (71, 73, 75, 77, 85, 86):
        return ("Snow", "bi-cloud-snow")
    if code in (95, 96, 99):
        return ("Thunderstorms", "bi-cloud-lightning-rain")
    return ("Mixed conditions", "bi-cloud")


def _request_json(url, params, cache_key, ttl=600):
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        response = requests.get(
            url,
            params=params,
            timeout=(3, 7),
            headers={
                "User-Agent": "SkyAwarePH-EducationalDashboard/1.0"
            },
        )

        response.raise_for_status()
        result = response.json()

        if not isinstance(result, dict) or result.get("error"):
            return None

        cache.set(cache_key, result, ttl)
        return result

    except (requests.RequestException, ValueError):
        return None


def _find_ph_city(city_name):
    key = hashlib.sha256(
        city_name.casefold().encode("utf-8")
    ).hexdigest()[:20]

    payload = _request_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {
            "name": city_name,
            "count": 5,
            "language": "en",
            "countryCode": "PH",
        },
        f"skyaware:city:{key}",
        ttl=86400,
    )

    results = (payload.get("results") or []) if payload else []

    for place in results:
        if (
            place.get("country_code") == "PH"
            and place.get("latitude") is not None
            and place.get("longitude") is not None
        ):
            return {
                "name": place.get("name", city_name),
                "region": (
                    place.get("admin1")
                    or place.get("admin2")
                    or "Philippines"
                ),
                "latitude": float(place["latitude"]),
                "longitude": float(place["longitude"]),
            }

    return None


def _weather_for(city):
    payload = _request_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": (
                "temperature_2m,relative_humidity_2m,"
                "apparent_temperature,wind_speed_10m,"
                "weather_code,precipitation"
            ),
            "daily": (
                "weather_code,temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "timezone": "Asia/Manila",
            "forecast_days": 7,
        },
        f"skyaware:forecast:{city['latitude']}:{city['longitude']}",
    )

    if not payload:
        return None

    now = payload.get("current") or {}
    daily = payload.get("daily") or {}

    condition, icon = _weather_condition(now.get("weather_code"))

    days = []
    dates = daily.get("time") or []

    for i, iso_date in enumerate(dates[:7]):

        def at(field):
            values = daily.get(field) or []
            return values[i] if i < len(values) else None

        try:
            day_label = datetime.strptime(
                iso_date, "%Y-%m-%d"
            ).strftime("%a")
        except (ValueError, TypeError):
            day_label = "Day"

        day_condition, day_icon = _weather_condition(
            at("weather_code")
        )

        days.append({
            "day": day_label,
            "high": at("temperature_2m_max"),
            "low": at("temperature_2m_min"),
            "rain": at("precipitation_probability_max"),
            "condition": day_condition,
            "icon": day_icon,
        })

    return {
        "temperature": now.get("temperature_2m"),
        "feels_like": now.get("apparent_temperature"),
        "humidity": now.get("relative_humidity_2m"),
        "wind": now.get("wind_speed_10m"),
        "precipitation": now.get("precipitation"),
        "condition": condition,
        "icon": icon,
        "days": days,
        "rain_chance": days[0]["rain"] if days else None,
    }


def _air_quality_for(city):
    payload = _request_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": "us_aqi,pm2_5,pm10",
            "timezone": "Asia/Manila",
        },
        f"skyaware:air:{city['latitude']}:{city['longitude']}",
    )

    if not payload:
        return None

    current = payload.get("current") or {}
    value = current.get("us_aqi")

    if value is None:
        category, tone, advice = (
            "Not available",
            "secondary",
            "Air quality data is unavailable for this location.",
        )
    elif value <= 50:
        category, tone, advice = (
            "Good",
            "good",
            "Air quality is generally satisfactory.",
        )
    elif value <= 100:
        category, tone, advice = (
            "Moderate",
            "moderate",
            "Unusually sensitive people may wish to limit prolonged outdoor activity.",
        )
    elif value <= 150:
        category, tone, advice = (
            "Unhealthy for sensitive groups",
            "sensitive",
            "Sensitive groups should reduce prolonged outdoor activity.",
        )
    elif value <= 200:
        category, tone, advice = (
            "Unhealthy",
            "unhealthy",
            "Limit prolonged outdoor activity, especially for sensitive groups.",
        )
    elif value <= 300:
        category, tone, advice = (
            "Very unhealthy",
            "very-unhealthy",
            "Avoid prolonged outdoor activity where possible.",
        )
    else:
        category, tone, advice = (
            "Hazardous",
            "hazardous",
            "Avoid outdoor physical activity where possible.",
        )

    return {
        "aqi": value,
        "marker_pct": (
            round(min(max(float(value) / 500 * 100, 0), 100))
            if value is not None else 0
        ),
        "pm25": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "category": category,
        "tone": tone,
        "advice": advice,
    }


def _recent_ph_earthquakes():
    today = timezone.now()

    payload = _request_json(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        {
            "format": "geojson",
            "minlatitude": 4,
            "maxlatitude": 22,
            "minlongitude": 116,
            "maxlongitude": 127,
            "minmagnitude": 3,
            "starttime": (
                today - timedelta(days=14)
            ).strftime("%Y-%m-%d"),
            "orderby": "time",
            "limit": 8,
        },
        "skyaware:ph-earthquakes-v1",
        ttl=600,
    )

    if payload is None:
        return [], False

    output = []

    for feature in (payload.get("features") or [])[:8]:
        props = feature.get("properties") or {}
        coords = (
            (feature.get("geometry") or {}).get("coordinates")
            or []
        )

        if len(coords) < 3 or props.get("mag") is None:
            continue

        event_time = props.get("time")

        try:
            local_time = timezone.localtime(
                datetime.fromtimestamp(
                    event_time / 1000,
                    tz=dt_timezone.utc,
                )
            ).strftime("%b %d, %I:%M %p")

        except (TypeError, ValueError, OverflowError):
            local_time = "Time unavailable"

        try:
            mag = float(props["mag"])
            lon, lat, depth = map(float, coords[:3])
        except (ValueError, TypeError):
            continue

        link = props.get("url") or ""

        output.append({
            "place": (
                props.get("place")
                or "Location not specified"
            ),
            "magnitude": round(mag, 1),
            "depth": round(depth, 1),
            "time": local_time,
            "latitude": lat,
            "longitude": lon,
            "url": (
                link
                if link.startswith("https://earthquake.usgs.gov/")
                else ""
            ),
            "tone": (
                "strong" if mag >= 5
                else "medium" if mag >= 4
                else "low"
            ),
        })

    return output, True


# ==========================================
# REGULAR USER DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):

    user_locations = SavedLocation.objects.filter(
        user=request.user
    )

    recent_locations = user_locations.order_by("-pk")[:5]

    user_donations = Donation.objects.filter(
        user=request.user
    )

    requested_city = (
        request.GET.get("city") or "Iligan"
    ).strip()[:80]

    if len(requested_city) < 2:
        requested_city = "Iligan"

    city = _find_ph_city(requested_city)

    weather = _weather_for(city) if city else None

    air_quality = _air_quality_for(city) if city else None

    earthquakes, earthquake_available = (
        _recent_ph_earthquakes()
    )

    map_data = {
        "city": city,
        "rain_mm": (
            weather.get("precipitation")
            if weather else None
        ),
        "aqi": (
            air_quality.get("aqi")
            if air_quality else None
        ),
        "earthquakes": [
            {
                "place": q["place"],
                "latitude": q["latitude"],
                "longitude": q["longitude"],
                "magnitude": q["magnitude"],
                "depth": q["depth"],
            }
            for q in earthquakes
        ],
    }

    context = {
        "total_user_locations": user_locations.count(),
        "recent_locations": recent_locations,
        "total_user_donations": user_donations.count(),
        "pending_user_donations": user_donations.filter(
            status=Donation.Status.PENDING
        ).count(),
        "searched_city": requested_city,
        "city": city,
        "weather": weather,
        "air_quality": air_quality,
        "earthquakes": earthquakes,
        "earthquake_available": earthquake_available,
        "map_data": map_data,
    }

    return render(
        request,
        "dashboard/index.html",
        context,
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@staff_member_required(login_url="login")
def admin_dashboard_view(request):

    User = get_user_model()

    total_users = User.objects.count()

    active_users = User.objects.filter(
        is_active=True
    ).count()

    admin_users = User.objects.filter(
        is_staff=True
    ).count()

    total_saved_locations = SavedLocation.objects.count()

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:5]

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

    paymongo_key = getattr(
        settings,
        "PAYMONGO_SECRET_KEY",
        "",
    )

    paymongo_configured = (
        isinstance(paymongo_key, str)
        and paymongo_key.startswith("sk_test_")
        and len(paymongo_key) > len("sk_test_")
    )

    paymongo_status = (
        "Configured"
        if paymongo_configured
        else "Not Configured"
    )

    # Integrated does not mean API uptime was checked.
    api_integrations = [
        {
            "name": "Open-Meteo Weather",
            "status": "Integrated",
        },
        {
            "name": "Open-Meteo Geocoding",
            "status": "Integrated",
        },
        {
            "name": "Open-Meteo Air Quality",
            "status": "Integrated",
        },
        {
            "name": "USGS Earthquake",
            "status": "Integrated",
        },
        {
            "name": "Groq AI Assistant",
            "status": "Integrated",
        },
        {
            "name": "PayMongo Test Checkout",
            "status": paymongo_status,
        },
    ]

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
        context,
    )
