
from datetime import (
    datetime,
    timedelta,
    timezone as dt_timezone
)

import requests

from django.contrib import messages
from django.contrib.admin.views.decorators import (
    staff_member_required
)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone

from weather.models import SavedLocation

# NEW: Nominatim geocoding
from integrations.nominatim import find_ph_city


# ==========================================
# API REQUEST HELPER
# ==========================================

def get_api_json(
    url,
    params,
    cache_key,
    timeout=8
):

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

        if (
            not isinstance(data, dict)
            or data.get("error")
        ):
            return None

        cache.set(
            cache_key,
            data,
            600
        )

        return data

    except (
        requests.RequestException,
        ValueError
    ):

        return None


# ==========================================
# WEATHER API
# OPEN-METEO
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

    current = data.get("current") or {}
    daily = data.get("daily") or {}

    weather_code = current.get(
        "weather_code"
    )

    # Weather condition and icon
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

    for index, day in enumerate(dates[:7]):

        def daily_value(field):

            values = daily.get(field) or []

            if index < len(values):
                return values[index]

            return None

        try:

            day_name = datetime.strptime(
                day,
                "%Y-%m-%d"
            ).strftime("%a")

        except (ValueError, TypeError):

            day_name = "Day"

        forecast.append({
            "day": day_name,
            "high": daily_value(
                "temperature_2m_max"
            ),
            "low": daily_value(
                "temperature_2m_min"
            ),
            "rain": daily_value(
                "precipitation_probability_max"
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

    current = data.get("current") or {}
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
# RECENT EARTHQUAKES
# USGS EARTHQUAKE API
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
        f"skyaware:recent-earthquakes:{start_date}"
    )

    if data is None:
        return None

    earthquakes = []

    for event in (
        data.get("features") or []
    )[:8]:

        properties = event.get(
            "properties"
        ) or {}

        geometry = event.get(
            "geometry"
        ) or {}

        coordinates = geometry.get(
            "coordinates"
        ) or []

        if (
            len(coordinates) < 3
            or properties.get("mag") is None
        ):
            continue

        try:

            magnitude = float(
                properties["mag"]
            )

            longitude = float(
                coordinates[0]
            )

            latitude = float(
                coordinates[1]
            )

            depth = float(
                coordinates[2]
            )

            event_time = datetime.fromtimestamp(
                properties["time"] / 1000,
                tz=dt_timezone.utc
            )

            formatted_time = timezone.localtime(
                event_time
            ).strftime(
                "%b %d, %I:%M %p"
            )

        except (
            TypeError,
            ValueError,
            KeyError,
            OverflowError
        ):
            continue

        earthquakes.append({
            "place": properties.get(
                "place"
            ) or "Unknown Location",
            "magnitude": magnitude,
            "depth": depth,
            "latitude": latitude,
            "longitude": longitude,
            "time": formatted_time,
        })

    return earthquakes


# ==========================================
# USER DASHBOARD
# ==========================================

@login_required
def dashboard_view(request):

    # Saved Locations CRUD data
    user_locations = SavedLocation.objects.filter(
        user=request.user
    )

    # Default city
    city_name = (
        request.GET.get("city") or "Iligan"
    ).strip()[:80]

    if len(city_name) < 2:
        city_name = "Iligan"

    city = None

    # ======================================
    # NOMINATIM LOCATION SEARCH
    # ======================================

    try:

        city = find_ph_city(
            city_name
        )

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ):

        messages.warning(
            request,
            "Location search is temporarily unavailable. "
            "Please try again later."
        )

    # Weather and air quality
    weather = get_weather(city)

    air_quality = get_air_quality(city)

    # Earthquake monitoring
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

    total_saved_locations = (
        SavedLocation.objects.count()
    )

    recent_users = User.objects.order_by(
        "-date_joined"
    )[:5]

    # Status reflects code integration,
    # not live API uptime.
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
