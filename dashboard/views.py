
from datetime import datetime, timedelta, timezone as dt_timezone
import hashlib

import requests

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone

from weather.models import SavedLocation


# ==========================================
# API REQUEST HELPER
# ==========================================

def get_api_json(url, params, cache_key, timeout=8):
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "User-Agent": "SkyAwarePH-SchoolProject/1.0"
            }
        )

        response.raise_for_status()
        data = response.json()

        if not isinstance(data, dict) or data.get("error"):
            return None

        cache.set(cache_key, data, 600)
        return data

    except (requests.RequestException, ValueError):
        return None


# ==========================================
# CITY GEOCODING
# Existing Open-Meteo geocoding.
# Nominatim will replace this later.
# ==========================================

def find_city(city_name):
    city_key = hashlib.sha256(
        city_name.lower().encode("utf-8")
    ).hexdigest()[:16]

    data = get_api_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {
            "name": city_name,
            "count": 5,
            "language": "en",
            "countryCode": "PH",
        },
        f"skyaware:city:{city_key}"
    )

    if not data:
        return None

    for place in data.get("results", []):
        if (
            place.get("country_code") == "PH"
            and place.get("latitude") is not None
            and place.get("longitude") is not None
        ):
            return {
                "name": place.get("name", city_name),
                "region": place.get("admin1", "Philippines"),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
            }

    return None


# ==========================================
# WEATHER API
# ==========================================

def get_weather(city):
    if not city:
        return None

    data = get_api_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "wind_speed_10m,"
                "weather_code"
            ),
            "daily": (
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "forecast_days": 7,
            "timezone": "Asia/Manila",
        },
        (
            f"skyaware:weather:"
            f"{city['latitude']}:{city['longitude']}"
        )
    )

    if not data:
        return None

    current = data.get("current", {})
    daily = data.get("daily", {})

    code = current.get("weather_code")

    if code == 0:
        condition = "Clear Sky"
        icon = "bi-sun"
    elif code in (1, 2):
        condition = "Partly Cloudy"
        icon = "bi-cloud-sun"
    elif code == 3:
        condition = "Cloudy"
        icon = "bi-clouds"
    elif code in (45, 48):
        condition = "Foggy"
        icon = "bi-cloud-fog"
    elif code in (
        51, 53, 55, 61, 63, 65, 80, 81, 82
    ):
        condition = "Rainy"
        icon = "bi-cloud-rain"
    elif code in (95, 96, 99):
        condition = "Thunderstorm"
        icon = "bi-cloud-lightning-rain"
    else:
        condition = "Weather Conditions"
        icon = "bi-cloud-sun"

    forecast = []

    for index, day in enumerate(daily.get("time", [])[:7]):

        def daily_value(field):
            values = daily.get(field, [])
            return (
                values[index]
                if index < len(values)
                else None
            )

        try:
            day_name = datetime.strptime(
                day, "%Y-%m-%d"
            ).strftime("%a")
        except (TypeError, ValueError):
            day_name = "Day"

        forecast.append({
            "day": day_name,
            "high": daily_value("temperature_2m_max"),
            "low": daily_value("temperature_2m_min"),
            "rain": daily_value(
                "precipitation_probability_max"
            ),
        })

    return {
        "temperature": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind": current.get("wind_speed_10m"),
        "condition": condition,
        "icon": icon,
        "forecast": forecast,
    }


# ==========================================
# AIR QUALITY API
# ==========================================

def get_air_quality(city):
    if not city:
        return None

    data = get_api_json(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": "us_aqi,pm2_5,pm10",
            "timezone": "Asia/Manila",
        },
        (
            f"skyaware:air:"
            f"{city['latitude']}:{city['longitude']}"
        )
    )

    if not data:
        return None

    current = data.get("current", {})

    aqi = current.get("us_aqi")

    if aqi is None:
        category = "Unavailable"
        status_class = "secondary"
    elif aqi <= 50:
        category = "Good"
        status_class = "success"
    elif aqi <= 100:
        category = "Moderate"
        status_class = "warning"
    elif aqi <= 150:
        category = "Unhealthy for Sensitive Groups"
        status_class = "warning"
    elif aqi <= 200:
        category = "Unhealthy"
        status_class = "danger"
    elif aqi <= 300:
        category = "Very Unhealthy"
        status_class = "danger"
    else:
        category = "Hazardous"
        status_class = "danger"

    return {
        "aqi": aqi,
        "pm25": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "category": category,
        "status_class": status_class,
    }


# ==========================================
# RECENT PHILIPPINE EARTHQUAKES
# ==========================================

def get_recent_earthquakes():
    start_date = (
        timezone.now() - timedelta(days=14)
    ).strftime("%Y-%m-%d")

    data = get_api_json(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        {
            "format": "geojson",
            "minlatitude": 4,
            "maxlatitude": 22,
            "minlongitude": 116,
            "maxlongitude": 127,
            "minmagnitude": 3,
            "starttime": start_date,
            "orderby": "time",
            "limit": 8,
        },
        "skyaware:recent-earthquakes-v2"
    )

    if data is None:
        return None

    earthquakes = []

    for event in data.get("features", [])[:8]:
        properties = event.get("properties") or {}
        geometry = event.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        if (
            len(coordinates) < 3
            or properties.get("mag") is None
        ):
            continue

        try:
            magnitude = float(properties["mag"])
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])
            depth = float(coordinates[2])

            event_time = datetime.fromtimestamp(
                properties["time"] / 1000,
                tz=dt_timezone.utc
            )

            formatted_time = timezone.localtime(
                event_time
            ).strftime("%b %d, %I:%M %p")

        except (TypeError, ValueError, OverflowError):
            continue

        earthquakes.append({
            "place": properties.get(
                "place",
                "Unknown Location"
            ),
            "magnitude": magnitude,
            "depth": depth,
            "latitude": latitude,
            "longitude": longitude,
            "time": formatted_time,
        })

    return earthquakes


# ==========================================
# REGULAR USER DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):

    user_locations = SavedLocation.objects.filter(
        user=request.user
    )

    city_name = (
        request.GET.get("city") or "Iligan"
    ).strip()[:80]

    if len(city_name) < 2:
        city_name = "Iligan"

    city = find_city(city_name)

    weather = get_weather(city)
    air_quality = get_air_quality(city)
    earthquakes = get_recent_earthquakes()

    context = {
        "searched_city": city_name,
        "city": city,
        "weather": weather,
        "air_quality": air_quality,
        "earthquakes": earthquakes,
        "total_user_locations": user_locations.count(),
        "recent_locations": user_locations.order_by(
            "-pk"
        )[:5],
    }

    return render(
        request,
        "dashboard/index.html",
        context
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

    # Statuses reflect implementation progress,
    # not live provider uptime checks.
    api_integrations = [
        {
            "name": "Open-Meteo",
            "purpose": "Weather and Air Quality",
            "status": "Integrated",
        },
        {
            "name": "USGS Earthquake",
            "purpose": "Earthquake Monitoring",
            "status": "Integrated",
        },
        {
            "name": "Groq AI",
            "purpose": "Disaster Safety Assistant",
            "status": "Integrated",
        },
        {
            "name": "NASA EONET",
            "purpose": "Natural Events",
            "status": "Planned",
        },
        {
            "name": "OpenStreetMap Nominatim",
            "purpose": "City Geocoding",
            "status": "Planned",
        },
    ]

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "total_saved_locations": total_saved_locations,
        "recent_users": recent_users,
        "api_integrations": api_integrations,
    }

    return render(
        request,
        "dashboard/admin_dashboard.html",
        context
    )
