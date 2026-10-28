
import requests

from django.core.cache import cache


AIR_QUALITY_URL = (
    "https://air-quality-api.open-meteo.com/v1/air-quality"
)


def get_aqi_category(aqi):
    """
    European Air Quality Index categories.
    """
    if aqi is None:
        return {
            "label": "Unavailable",
            "color": "secondary",
            "advice": "Air quality data is not available."
        }

    if aqi <= 20:
        return {
            "label": "Good",
            "color": "success",
            "advice": (
                "Air quality is generally good. "
                "Normal outdoor activities are suitable."
            )
        }

    if aqi <= 40:
        return {
            "label": "Fair",
            "color": "info",
            "advice": (
                "Air quality is generally acceptable. "
                "Sensitive individuals should monitor symptoms."
            )
        }

    if aqi <= 60:
        return {
            "label": "Moderate",
            "color": "warning",
            "advice": (
                "People sensitive to air pollution may "
                "consider reducing prolonged outdoor exertion."
            )
        }

    if aqi <= 80:
        return {
            "label": "Poor",
            "color": "warning",
            "advice": (
                "Consider reducing strenuous outdoor activities, "
                "especially if you are sensitive to pollution."
            )
        }

    if aqi <= 100:
        return {
            "label": "Very Poor",
            "color": "danger",
            "advice": (
                "Limit strenuous outdoor activity and "
                "consider staying indoors when possible."
            )
        }

    return {
        "label": "Extremely Poor",
        "color": "danger",
        "advice": (
            "Avoid unnecessary outdoor exertion. "
            "Follow local public health guidance."
        )
    }


def get_air_quality(latitude, longitude):
    """
    Fetch current air quality for a selected location.
    """

    cache_key = f"air_quality_{latitude}_{longitude}"

    cached = cache.get(cache_key)

    if cached is not None:
        return cached

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "european_aqi,pm2_5,pm10,"
            "carbon_monoxide,nitrogen_dioxide,"
            "ozone,sulphur_dioxide"
        ),
        "timezone": "Asia/Manila"
    }

    response = requests.get(
        AIR_QUALITY_URL,
        params=params,
        timeout=15
    )

    response.raise_for_status()

    data = response.json()

    current = data.get("current") or {}

    aqi = current.get("european_aqi")

    category = get_aqi_category(aqi)

    result = {
        "current": current,
        "aqi": aqi,
        "category": category,
        "timezone": data.get("timezone"),
        "units": data.get("current_units") or {}
    }

    # Cache for 10 minutes
    cache.set(cache_key, result, 600)

    return result
