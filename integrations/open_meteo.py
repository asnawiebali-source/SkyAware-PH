
import os
import logging
import requests

from django.core.cache import cache


logger = logging.getLogger(__name__)

GEOCODING_URL = (
    "https://geocoding-api.open-meteo.com/v1/search"
)

FORECAST_URL = (
    "https://api.open-meteo.com/v1/forecast"
)

VISUAL_CROSSING_URL = (
    "https://weather.visualcrossing.com/"
    "VisualCrossingWebServices/rest/services/timeline"
)

# Cache successful weather data for 15 minutes.
WEATHER_CACHE_SECONDS = 900

# Avoid repeating Open-Meteo requests during rate limits.
RATE_LIMIT_COOLDOWN = 3600


WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Dense freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snowfall", "❄️"),
    73: ("Moderate snowfall", "❄️"),
    75: ("Heavy snowfall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "❄️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


VISUAL_ICONS = {
    "clear-day": (0, "Clear sky", "☀️"),
    "clear-night": (0, "Clear sky", "🌙"),
    "partly-cloudy-day": (2, "Partly cloudy", "⛅"),
    "partly-cloudy-night": (2, "Partly cloudy", "☁️"),
    "cloudy": (3, "Cloudy", "☁️"),
    "rain": (61, "Rainy", "🌧️"),
    "showers-day": (80, "Rain showers", "🌦️"),
    "showers-night": (80, "Rain showers", "🌧️"),
    "thunder-rain": (95, "Thunderstorm", "⛈️"),
    "thunder-showers-day": (95, "Thunderstorm", "⛈️"),
    "thunder-showers-night": (95, "Thunderstorm", "⛈️"),
    "fog": (45, "Fog", "🌫️"),
    "snow": (71, "Snow", "❄️"),
    "snow-showers-day": (85, "Snow showers", "❄️"),
    "snow-showers-night": (85, "Snow showers", "❄️"),
    "wind": (2, "Windy", "💨"),
}


def get_weather_description(code):
    return WEATHER_CODES.get(
        code,
        ("Unknown conditions", "🌡️"),
    )


def search_city(city_name):
    """
    Existing Open-Meteo geocoding helper.
    Retained for compatibility.
    """
    cache_key = f"weather_city_{city_name.lower().strip()}"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    params = {
        "name": city_name,
        "count": 10,
        "language": "en",
        "countryCode": "PH",
    }

    response = requests.get(
        GEOCODING_URL,
        params=params,
        timeout=10,
    )
    response.raise_for_status()

    results = response.json().get("results", [])

    if not results:
        return None

    city = next(
        (
            result
            for result in results
            if result["name"].casefold()
            == city_name.strip().casefold()
        ),
        results[0],
    )

    cache.set(cache_key, city, 3600)

    return city


def get_open_meteo_weather(latitude, longitude):
    """
    Primary weather provider.
    Returns the existing SkyAware PH format.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "timezone": "Asia/Manila",
        "forecast_days": 7,
    }

    response = requests.get(
        FORECAST_URL,
        params=params,
        timeout=15,
    )

    # Respect the provider's rate limit.
    if response.status_code == 429:
        cache.set(
            "skyaware:open_meteo:rate_limited",
            True,
            RATE_LIMIT_COOLDOWN,
        )

        logger.warning(
            "Open-Meteo returned HTTP 429. "
            "Switching to backup weather provider."
        )

        return None

    response.raise_for_status()

    data = response.json()

    current = data.get("current") or {}
    daily = data.get("daily") or {}

    if (
        current.get("temperature_2m") is None
        or not daily.get("time")
    ):
        return None

    description, icon = get_weather_description(
        current.get("weather_code")
    )

    forecast = []

    for index, date in enumerate(daily["time"][:7]):

        code = daily["weather_code"][index]

        day_description, day_icon = (
            get_weather_description(code)
        )

        forecast.append({
            "date": date,
            "description": day_description,
            "icon": day_icon,
            "max_temp": (
                daily["temperature_2m_max"][index]
            ),
            "min_temp": (
                daily["temperature_2m_min"][index]
            ),
            "rain_probability": (
                daily["precipitation_probability_max"][index]
            ),
        })

    return {
        "current": current,
        "description": description,
        "icon": icon,
        "forecast": forecast,
        "timezone": data.get("timezone"),
        "source": "Open-Meteo",
    }


def get_visual_crossing_weather(latitude, longitude):
    """
    Backup provider for current weather
    and seven-day forecasts.
    """
    api_key = os.getenv(
        "VISUAL_CROSSING_API_KEY",
        "",
    ).strip()

    if not api_key:
        logger.warning(
            "Visual Crossing API key is missing."
        )
        return None

    location = f"{latitude},{longitude}"

    url = f"{VISUAL_CROSSING_URL}/{location}"

    params = {
        "key": api_key,
        "unitGroup": "metric",
        "include": "current,days",
        "contentType": "json",
        "lang": "en",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15,
        )

        # Avoid logging the response URL because
        # its query string contains the API key.
        if response.status_code != 200:
            logger.warning(
                "Visual Crossing returned HTTP %s",
                response.status_code,
            )
            return None

        data = response.json()

    except (requests.RequestException, ValueError) as exc:
        logger.warning(
            "Visual Crossing request failed: %s",
            type(exc).__name__,
        )
        return None

    current_data = data.get("currentConditions") or {}
    days = data.get("days") or []

    if current_data.get("temp") is None or not days:
        logger.warning(
            "Visual Crossing returned incomplete weather data."
        )
        return None

    condition_code, description, icon = VISUAL_ICONS.get(
        current_data.get("icon"),
        (None, "Weather conditions", "🌤️"),
    )

    current_time = current_data.get("datetime", "")

    if current_time and days:
        current_time = (
            f"{days[0].get('datetime', '')}T"
            f"{current_time}"
        )

    current = {
        "temperature_2m": current_data.get("temp"),
        "relative_humidity_2m": current_data.get("humidity"),
        "apparent_temperature": current_data.get("feelslike"),
        "precipitation": current_data.get("precip"),
        "weather_code": condition_code,
        "wind_speed_10m": current_data.get("windspeed"),
        "time": current_time,
    }

    forecast = []

    for day in days[:7]:

        _, day_description, day_icon = VISUAL_ICONS.get(
            day.get("icon"),
            (None, "Weather conditions", "🌤️"),
        )

        forecast.append({
            "date": day.get("datetime"),
            "description": day.get(
                "conditions",
                day_description,
            ),
            "icon": day_icon,
            "max_temp": day.get("tempmax"),
            "min_temp": day.get("tempmin"),
            "rain_probability": day.get("precipprob"),
        })

    return {
        "current": current,
        "description": current_data.get(
            "conditions",
            description,
        ),
        "icon": icon,
        "forecast": forecast,
        "timezone": data.get(
            "timezone",
            "Asia/Manila",
        ),
        "source": "Visual Crossing",
    }


def get_weather(latitude, longitude):
    """
    Shared weather entry point.

    1. Try cached weather.
    2. Use Open-Meteo when available.
    3. Fall back to Visual Crossing.
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (ValueError, TypeError):
        return None

    # Use rounded coordinates for shared caching.
    cache_key = f"skyaware:weather:v3:{lat:.5f}:{lon:.5f}"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    result = None

    rate_limited = cache.get(
        "skyaware:open_meteo:rate_limited"
    )

    if not rate_limited:
        try:
            result = get_open_meteo_weather(
                lat,
                lon,
            )

        except (requests.RequestException, ValueError) as exc:
            logger.warning(
                "Open-Meteo unavailable: %s",
                type(exc).__name__,
            )

    if result is None:
        result = get_visual_crossing_weather(
            lat,
            lon,
        )

    if result is not None:
        cache.set(
            cache_key,
            result,
            WEATHER_CACHE_SECONDS,
        )

    return result
