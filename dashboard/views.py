
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render

from weather.models import SavedLocation

from integrations.nominatim import find_ph_city
from integrations.usgs_earthquake import (
    get_recent_earthquakes as fetch_usgs_earthquakes
)


# ==========================================
# SETTINGS
# ==========================================

WEATHER_CACHE_SECONDS = 600
AIR_QUALITY_CACHE_SECONDS = 600

# Avoid repeatedly calling an unavailable
# API on every page refresh.
FAILURE_CACHE_SECONDS = 30

# Separate connection and read timeouts.
API_TIMEOUT = (3, 5)


# ==========================================
# REUSABLE API REQUEST HELPER
# ==========================================

def get_api_json(
    url,
    params,
    cache_key,
    timeout=API_TIMEOUT,
    cache_seconds=600,
):
    """
    Fetch JSON with caching and error handling.

    A successful result is cached to avoid
    unnecessary repeated external requests.

    If an API fails, requests for the same
    resource are briefly paused.
    """

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    failure_key = f"{cache_key}:failed"

    if cache.get(failure_key):
        return None

    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={
                "User-Agent": (
                    "SkyAwarePH/1.0 "
                    "educational-weather-portal"
                ),
                "Accept": "application/json",
            },
        )

        response.raise_for_status()

        data = response.json()

        if (
            not isinstance(data, dict)
            or data.get("error")
        ):
            cache.set(
                failure_key,
                True,
                FAILURE_CACHE_SECONDS
            )
            return None

        cache.set(
            cache_key,
            data,
            cache_seconds
        )

        return data

    except (
        requests.RequestException,
        ValueError,
    ):
        cache.set(
            failure_key,
            True,
            FAILURE_CACHE_SECONDS
        )

        return None


# ==========================================
# CITY COORDINATES CACHE KEY
# ==========================================

def city_cache_suffix(city):
    """
    Consistent cache key for a location.
    """

    try:
        latitude = float(city["latitude"])
        longitude = float(city["longitude"])

        return (
            f"{latitude:.5f}:"
            f"{longitude:.5f}"
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ):
        return None


# ==========================================
# WEATHER API
# OPEN-METEO
# ==========================================

def get_weather(city):

    if not city:
        return None

    location_key = city_cache_suffix(city)

    if location_key is None:
        return None

    data = get_api_json(
        url=(
            "https://api.open-meteo.com/v1/forecast"
        ),
        params={
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
        cache_key=(
            "skyaware:dashboard:"
            f"weather:v2:{location_key}"
        ),
        cache_seconds=WEATHER_CACHE_SECONDS,
    )

    if not data:
        return None

    current = data.get("current") or {}
    daily = data.get("daily") or {}

    weather_code = current.get(
        "weather_code"
    )

    # ======================================
    # WEATHER DESCRIPTION
    # ======================================

    if weather_code == 0:
        condition = "Clear Sky"
        icon = "bi-sun"

    elif weather_code in (1, 2):
        condition = "Partly Cloudy"
        icon = "bi-cloud-sun"

    elif weather_code == 3:
        condition = "Cloudy"
        icon = "bi-clouds"

    elif weather_code in (45, 48):
        condition = "Foggy"
        icon = "bi-cloud-fog"

    elif weather_code in (
        51, 53, 55,
        61, 63, 65,
        80, 81, 82
    ):
        condition = "Rainy"
        icon = "bi-cloud-rain"

    elif weather_code in (95, 96, 99):
        condition = "Thunderstorm"
        icon = "bi-cloud-lightning-rain"

    else:
        condition = "Weather Conditions"
        icon = "bi-cloud-sun"

    # ======================================
    # SEVEN DAY FORECAST
    # ======================================

    forecast = []

    dates = daily.get("time") or []

    def get_daily_value(field, index):

        values = daily.get(field) or []

        if index < len(values):
            return values[index]

        return None

    for index, day in enumerate(dates[:7]):

        try:
            day_name = datetime.strptime(
                day,
                "%Y-%m-%d"
            ).strftime("%a")

        except (ValueError, TypeError):
            day_name = "Day"

        forecast.append({
            "day": day_name,
            "high": get_daily_value(
                "temperature_2m_max",
                index
            ),
            "low": get_daily_value(
                "temperature_2m_min",
                index
            ),
            "rain": get_daily_value(
                "precipitation_probability_max",
                index
            ),
        })

    return {
        "temperature": current.get(
            "temperature_2m"
        ),
        "feels_like": current.get(
            "apparent_temperature"
        ),
        "humidity": current.get(
            "relative_humidity_2m"
        ),
        "wind": current.get(
            "wind_speed_10m"
        ),
        "condition": condition,
        "icon": icon,
        "forecast": forecast,
    }


# ==========================================
# AIR QUALITY API
# OPEN-METEO
# ==========================================

def get_air_quality(city):

    if not city:
        return None

    location_key = city_cache_suffix(city)

    if location_key is None:
        return None

    data = get_api_json(
        url=(
            "https://air-quality-api.open-meteo.com/"
            "v1/air-quality"
        ),
        params={
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "current": "us_aqi,pm2_5,pm10",
            "timezone": "Asia/Manila",
        },
        cache_key=(
            "skyaware:dashboard:"
            f"air:v2:{location_key}"
        ),
        cache_seconds=AIR_QUALITY_CACHE_SECONDS,
    )

    if not data:
        return None

    current = data.get("current") or {}

    aqi = current.get("us_aqi")

    # ======================================
    # AIR QUALITY STATUS
    # ======================================

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
# USGS EARTHQUAKE API
# SHARED WITH EARTHQUAKE UPDATES PAGE
# ==========================================

def get_recent_earthquakes():
    """
    Dashboard preview:
    - Last 7 days
    - Magnitude 2.5+
    - Maximum 5 displayed earthquakes
    """

    try:
        data = fetch_usgs_earthquakes(
            days=7,
            min_magnitude=2.5
        )

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError,
    ):
        return None

    if not data:
        return None

    recent = []

    for quake in (
        data.get("earthquakes") or []
    )[:5]:

        # Convert date and time for the
        # smaller dashboard card.
        try:
            event_datetime = datetime.strptime(
                (
                    f"{quake['date']} "
                    f"{quake['time']}"
                ),
                "%B %d, %Y %I:%M %p"
            )

            display_time = (
                event_datetime.strftime(
                    "%b %d, %I:%M %p"
                )
            )

        except (
            ValueError,
            TypeError,
            KeyError,
        ):
            display_time = (
                f"{quake.get('date', '')}, "
                f"{quake.get('time', '')}"
            )

        recent.append({
            "id": quake.get("id"),
            "place": quake.get(
                "place",
                "Unknown location"
            ),
            "magnitude": quake.get(
                "magnitude"
            ),
            "depth": quake.get("depth"),
            "latitude": quake.get(
                "latitude"
            ),
            "longitude": quake.get(
                "longitude"
            ),
            "time": display_time,
        })

    return recent


# ==========================================
# CONCURRENT DASHBOARD API REQUESTS
# ==========================================

def fetch_dashboard_data(city):
    """
    Fetch independent API data concurrently.

    Previously:
        Weather -> Air Quality -> Earthquakes

    Now:
        Weather + Air Quality + Earthquakes

    This reduces waiting when several
    requests need fresh data at once.
    """

    with ThreadPoolExecutor(
        max_workers=3
    ) as executor:

        weather_future = executor.submit(
            get_weather,
            city
        )

        air_future = executor.submit(
            get_air_quality,
            city
        )

        earthquake_future = executor.submit(
            get_recent_earthquakes
        )

        try:
            weather = weather_future.result()

        except Exception:
            weather = None

        try:
            air_quality = air_future.result()

        except Exception:
            air_quality = None

        try:
            earthquakes = earthquake_future.result()

        except Exception:
            earthquakes = None

    return weather, air_quality, earthquakes


# ==========================================
# USER DASHBOARD
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

    city = None

    # ======================================
    # CITY GEOCODING
    # ======================================

    try:
        city = find_ph_city(city_name)

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        messages.warning(
            request,
            "Location search is temporarily "
            "unavailable. Please try again later."
        )

    # ======================================
    # CONCURRENT API DATA
    # ======================================

    (
        weather,
        air_quality,
        earthquakes
    ) = fetch_dashboard_data(city)

    # ======================================
    # DASHBOARD DATA
    # ======================================

    context = {
        "searched_city": city_name,
        "city": city,
        "weather": weather,
        "air_quality": air_quality,
        "earthquakes": earthquakes,

        "total_user_locations": (
            user_locations.count()
        ),

        "recent_locations": (
            user_locations.order_by("-pk")[:5]
        ),
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

    total_saved_locations = (
        SavedLocation.objects.count()
    )

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:5]

    # Status describes code integration,
    # not real-time API availability.
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
            "status": "Integrated",
        },
        {
            "name": "OpenStreetMap Nominatim",
            "purpose": "City Geocoding",
            "status": "Integrated",
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
