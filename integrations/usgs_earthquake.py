
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

from django.core.cache import cache


# ==========================================
# USGS CONFIGURATION
# ==========================================

USGS_API_URL = (
    "https://earthquake.usgs.gov/"
    "fdsnws/event/1/query"
)

PHILIPPINE_TIME = ZoneInfo("Asia/Manila")

CACHE_DURATION = 600

FAILURE_CACHE_DURATION = 30

# Connect timeout: 3 seconds
# Read timeout: 5 seconds
REQUEST_TIMEOUT = (3, 5)


# ==========================================
# GET RECENT EARTHQUAKES
# ==========================================

def get_recent_earthquakes(
    days=7,
    min_magnitude=2.5
):
    """
    Retrieve Philippine earthquake reports.

    Used by:
    - User Dashboard
    - Earthquake Updates page
    - Earthquake filters and map

    Supported examples:
    - Last 24 hours
    - Last 7 days
    - Last 14 days
    - Last 30 days
    """

    # ======================================
    # VALIDATE PARAMETERS
    # ======================================

    days = int(days)
    min_magnitude = float(min_magnitude)

    if days not in (1, 7, 14, 30):
        raise ValueError(
            "Unsupported earthquake search period."
        )

    if min_magnitude not in (2.5, 4.0, 6.0):
        raise ValueError(
            "Unsupported magnitude filter."
        )

    # ======================================
    # CHECK CACHE
    # ======================================

    cache_key = (
        f"usgs_ph_{days}_{min_magnitude}"
    )

    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return cached_data

    failure_key = f"{cache_key}:failed"

    # Avoid another expensive request immediately
    # after the same service has failed.
    if cache.get(failure_key):
        raise requests.ConnectionError(
            "USGS is temporarily unavailable."
        )

    # ======================================
    # REQUEST DATE RANGE
    # ======================================

    end_date = datetime.now(timezone.utc)

    start_date = (
        end_date - timedelta(days=days)
    )

    params = {
        "format": "geojson",

        "starttime": start_date.strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),

        "endtime": end_date.strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),

        # Philippines and nearby waters
        "minlatitude": 4,
        "maxlatitude": 22,
        "minlongitude": 116,
        "maxlongitude": 127,

        "minmagnitude": min_magnitude,
        "eventtype": "earthquake",
        "orderby": "time",
        "limit": 50,
    }

    # ======================================
    # FETCH USGS DATA
    # ======================================

    try:
        response = requests.get(
            USGS_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": (
                    "SkyAwarePH/1.0 "
                    "educational-project"
                ),
                "Accept": "application/geo+json",
            },
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            raise ValueError(
                "Invalid USGS response."
            )

    except (
        requests.RequestException,
        ValueError,
    ):
        cache.set(
            failure_key,
            True,
            FAILURE_CACHE_DURATION
        )
        raise

    # ======================================
    # PROCESS EARTHQUAKE RECORDS
    # ======================================

    earthquakes = []

    features = data.get("features") or []

    for feature in features:

        if not isinstance(feature, dict):
            continue

        properties = (
            feature.get("properties") or {}
        )

        geometry = (
            feature.get("geometry") or {}
        )

        if not isinstance(properties, dict):
            continue

        if not isinstance(geometry, dict):
            continue

        coordinates = (
            geometry.get("coordinates") or []
        )

        magnitude = properties.get("mag")
        timestamp = properties.get("time")

        if (
            magnitude is None
            or timestamp is None
        ):
            continue

        # ==================================
        # CONVERT EVENT VALUES
        # ==================================

        try:
            magnitude = float(magnitude)

            event_time = datetime.fromtimestamp(
                float(timestamp) / 1000,
                tz=timezone.utc
            ).astimezone(PHILIPPINE_TIME)

            longitude = (
                float(coordinates[0])
                if len(coordinates) > 0
                and coordinates[0] is not None
                else None
            )

            latitude = (
                float(coordinates[1])
                if len(coordinates) > 1
                and coordinates[1] is not None
                else None
            )

            depth = (
                float(coordinates[2])
                if len(coordinates) > 2
                and coordinates[2] is not None
                else None
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
            IndexError,
        ):
            continue

        # ==================================
        # BUILD EVENT RECORD
        # ==================================

        earthquakes.append({
            "id": feature.get("id"),
            "magnitude": magnitude,

            "place": (
                properties.get("place")
                or "Location not specified"
            ),

            "depth": depth,
            "latitude": latitude,
            "longitude": longitude,

            "date": event_time.strftime(
                "%B %d, %Y"
            ),

            "time": event_time.strftime(
                "%I:%M %p"
            ),

            "url": properties.get("url"),

            "status": properties.get(
                "status",
                "unknown"
            ),
        })

    # ======================================
    # BUILD RESPONSE
    # ======================================

    result = {
        "earthquakes": earthquakes,
        "count": len(earthquakes),
        "days": days,
        "min_magnitude": min_magnitude,

        "updated_at": datetime.now(
            PHILIPPINE_TIME
        ).strftime(
            "%B %d, %Y %I:%M %p"
        ),
    }

    # ======================================
    # CACHE SUCCESSFUL RESPONSE
    # ======================================

    cache.set(
        cache_key,
        result,
        CACHE_DURATION
    )

    cache.delete(failure_key)

    return result
