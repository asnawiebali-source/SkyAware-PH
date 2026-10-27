
import requests

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from django.core.cache import cache


USGS_API_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
)

PHILIPPINE_TIME = ZoneInfo("Asia/Manila")


def get_recent_earthquakes(days=7, min_magnitude=2.5):
    """
    Get recent reported earthquakes in and around
    the Philippines using the USGS Earthquake API.
    """

    cache_key = f"usgs_ph_{days}_{min_magnitude}"
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)

    params = {
        "format": "geojson",
        "starttime": start_date.strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "endtime": end_date.strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),
        "minlatitude": 4,
        "maxlatitude": 22,
        "minlongitude": 116,
        "maxlongitude": 127,
        "minmagnitude": min_magnitude,
        "eventtype": "earthquake",
        "orderby": "time",
        "limit": 50,
    }

    response = requests.get(
        USGS_API_URL,
        params=params,
        timeout=20,
        headers={
            "User-Agent": "SkyAwarePH/1.0 educational-project"
        }
    )

    response.raise_for_status()

    data = response.json()

    earthquakes = []

    for feature in data.get("features", []):
        properties = feature.get("properties", {})
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []

        magnitude = properties.get("mag")
        timestamp = properties.get("time")

        if magnitude is None or timestamp is None:
            continue

        event_time = datetime.fromtimestamp(
            timestamp / 1000,
            tz=timezone.utc
        ).astimezone(PHILIPPINE_TIME)

        longitude = (
            coordinates[0] if len(coordinates) > 0 else None
        )
        latitude = (
            coordinates[1] if len(coordinates) > 1 else None
        )
        depth = (
            coordinates[2] if len(coordinates) > 2 else None
        )

        earthquakes.append({
            "id": feature.get("id"),
            "magnitude": magnitude,
            "place": properties.get(
                "place"
            ) or "Location not specified",
            "depth": depth,
            "latitude": latitude,
            "longitude": longitude,
            "date": event_time.strftime("%B %d, %Y"),
            "time": event_time.strftime("%I:%M %p"),
            "url": properties.get("url"),
            "status": properties.get("status", "unknown"),
        })

    result = {
        "earthquakes": earthquakes,
        "count": len(earthquakes),
        "days": days,
        "min_magnitude": min_magnitude,
        "updated_at": datetime.now(
            PHILIPPINE_TIME
        ).strftime("%B %d, %Y %I:%M %p"),
    }

    # Cache results for five minutes.
    cache.set(cache_key, result, 300)

    return result
