
"""
SkyAware PH - OpenStreetMap Nominatim Integration

Searches Philippine cities and towns and returns
coordinates for weather and air quality requests.

Designed for a small, single-process school project.
"""

import hashlib
import os
import threading
import time

import requests

from django.core.cache import cache


# ==========================================
# NOMINATIM CONFIGURATION
# ==========================================

NOMINATIM_SEARCH_URL = os.getenv(
    "NOMINATIM_SEARCH_URL",
    "https://nominatim.openstreetmap.org/search"
)

USER_AGENT = (
    "SkyAwarePH/1.0 "
    "(educational weather portal; "
    "https://github.com/asnawiebali-source/SkyAware-PH)"
)

# Limit outgoing Nominatim requests.
# This lock works within one Python process.
REQUEST_LOCK = threading.Lock()
LAST_REQUEST = 0.0


# ==========================================
# SEARCH PHILIPPINE CITY
# ==========================================

def find_ph_city(city_name):

    global LAST_REQUEST

    # Validate input
    if not isinstance(city_name, str):
        return None

    city_name = " ".join(city_name.strip().split())

    if len(city_name) < 2 or len(city_name) > 100:
        return None

    # Create cache key
    city_hash = hashlib.sha256(
        city_name.casefold().encode("utf-8")
    ).hexdigest()

    cache_key = f"skyaware:nominatim:ph:v1:{city_hash}"

    # Check cached city
    cached = cache.get(cache_key)

    if cached is not None:
        return cached.get("city")

    # API parameters
    params = {
        "q": city_name,
        "format": "jsonv2",
        "countrycodes": "ph",
        "addressdetails": 1,
        "layer": "address",
        "limit": 5,
        "accept-language": "en",
    }

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    # ======================================
    # SEND NOMINATIM REQUEST
    # ======================================

    with REQUEST_LOCK:

        elapsed = time.monotonic() - LAST_REQUEST

        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)

        LAST_REQUEST = time.monotonic()

        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=15,
        )

    response.raise_for_status()

    results = response.json()

    if not isinstance(results, list):
        raise ValueError(
            "Invalid response from Nominatim API."
        )

    # ======================================
    # PROCESS LOCATION RESULTS
    # ======================================

    for result in results:

        if not isinstance(result, dict):
            continue

        address = result.get("address") or {}

        # Accept only locations in the Philippines
        if address.get("country_code") not in (
            None,
            "ph"
        ):
            continue

        try:
            latitude = float(result["lat"])
            longitude = float(result["lon"])

        except (
            KeyError,
            ValueError,
            TypeError,
        ):
            continue

        # Validate coordinates
        if not (
            -90 <= latitude <= 90
            and -180 <= longitude <= 180
        ):
            continue

        # Location name
        name = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("village")
            or result.get("name")
            or city_name
        )

        # Region / province
        region = (
            address.get("state")
            or address.get("province")
            or address.get("region")
            or "Philippines"
        )

        city = {
            "name": name,
            "region": region,
            "latitude": latitude,
            "longitude": longitude,
            "display_name": result.get(
                "display_name",
                city_name
            ),
        }

        # Cache successful results for 7 days
        cache.set(
            cache_key,
            {"city": city},
            7 * 24 * 60 * 60,
        )

        return city

    # Cache unsuccessful city search for 1 hour
    cache.set(
        cache_key,
        {"city": None},
        3600,
    )

    return None
