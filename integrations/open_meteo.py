
import requests

from django.core.cache import cache


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


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


def get_weather_description(code):
    return WEATHER_CODES.get(
        code, ("Unknown conditions", "🌡️")
    )


def search_city(city_name):
    """
    Search for a city in the Philippines.
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
        timeout=10
    )
    response.raise_for_status()

    results = response.json().get("results", [])

    if not results:
        return None

    # Prefer an exact city-name match when possible.
    city = next(
        (
            result for result in results
            if result["name"].casefold()
            == city_name.strip().casefold()
        ),
        results[0]
    )

    cache.set(cache_key, city, 3600)
    return city


def get_weather(latitude, longitude):
    """
    Retrieve current weather and 7-day forecast.
    """
    cache_key = f"weather_{latitude}_{longitude}"
    cached = cache.get(cache_key)

    if cached is not None:
        return cached

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
        timeout=15
    )
    response.raise_for_status()

    data = response.json()

    current = data.get("current", {})
    daily = data.get("daily", {})

    description, icon = get_weather_description(
        current.get("weather_code")
    )

    forecast = []

    dates = daily.get("time", [])

    for i, date in enumerate(dates):
        code = daily["weather_code"][i]
        day_description, day_icon = get_weather_description(code)

        forecast.append({
            "date": date,
            "description": day_description,
            "icon": day_icon,
            "max_temp": daily["temperature_2m_max"][i],
            "min_temp": daily["temperature_2m_min"][i],
            "rain_probability": (
                daily["precipitation_probability_max"][i]
            ),
        })

    result = {
        "current": current,
        "description": description,
        "icon": icon,
        "forecast": forecast,
        "timezone": data.get("timezone"),
    }

    # Cache results for 10 minutes.
    cache.set(cache_key, result, 600)

    return result
