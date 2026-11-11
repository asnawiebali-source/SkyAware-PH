
import hashlib
import os
import re
import threading
import time
import unicodedata

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
    "(educational weather and disaster portal; "
    "https://github.com/asnawiebali-source/SkyAware-PH)"
)

REQUEST_LOCK = threading.Lock()
LAST_REQUEST = 0.0

CACHE_DURATION = 7 * 24 * 60 * 60

# Verified reference fallback for Iligan only.
# Used if Nominatim fails to find the correct city.
# Other cities still use Nominatim.
ILIGAN_REFERENCE = {
    "name": "Iligan City",
    "region": "Northern Mindanao",
    "admin1": "Northern Mindanao",
    "province": "Lanao del Norte",
    "country": "Philippines",
    "latitude": 8.2286,
    "longitude": 124.2381,
    "display_name": (
        "Iligan City, Lanao del Norte, "
        "Northern Mindanao, Philippines"
    ),
}


# ==========================================
# NORMALIZE CITY NAMES
# ==========================================

def normalize_city_name(value):

    value = unicodedata.normalize(
        "NFKD",
        str(value or "")
    )

    value = "".join(
        ch for ch in value
        if not unicodedata.combining(ch)
    )

    value = value.casefold().strip()

    value = re.sub(
        r"^(city|municipality|town) of\s+",
        "",
        value
    )

    value = re.sub(
        r"\s+(city|municipality|town)$",
        "",
        value
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value
    )

    return " ".join(value.split())


# ==========================================
# THROTTLED NOMINATIM REQUEST
# ==========================================

def request_nominatim(params):

    global LAST_REQUEST

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    parameters = {
        "format": "jsonv2",
        "countrycodes": "ph",
        "addressdetails": 1,
        "layer": "address",
        "limit": 10,
        "accept-language": "en",
    }

    parameters.update(params)

    # Maximum one request per second
    # inside this Python process.
    with REQUEST_LOCK:

        elapsed = (
            time.monotonic() - LAST_REQUEST
        )

        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)

        LAST_REQUEST = time.monotonic()

        response = requests.get(
            NOMINATIM_SEARCH_URL,
            params=parameters,
            headers=headers,
            timeout=12,
        )

    response.raise_for_status()

    results = response.json()

    if not isinstance(results, list):
        raise ValueError(
            "Unexpected Nominatim response."
        )

    return results


# ==========================================
# CHECK WHETHER RESULT MATCHES THE CITY
# ==========================================

def get_matching_city(result, requested_name):

    if not isinstance(result, dict):
        return None

    address = result.get("address") or {}

    if address.get("country_code") != "ph":
        return None

    requested = normalize_city_name(
        requested_name
    )

    if not requested:
        return None

    # Only accept settlement-level results.
    # Avoid streets, buildings and other POIs.
    place_type = (
        result.get("addresstype")
        or result.get("type")
        or ""
    ).lower()

    allowed_types = {
        "city",
        "town",
        "municipality",
        "village",
        "hamlet",
        "administrative",
    }

    if place_type not in allowed_types:
        return None

    # A city or municipality in the address
    # must agree with the requested city.
    settlement = (
        address.get("city")
        or address.get("town")
        or address.get("municipality")
    )

    if settlement:

        if normalize_city_name(settlement) != requested:
            return None

    # Match the result's own settlement name.
    result_name = (
        result.get("name")
        or address.get("city")
        or address.get("town")
        or address.get("municipality")
        or address.get("village")
        or ""
    )

    if normalize_city_name(result_name) != requested:

        # Some administrative city boundaries
        # have an unusual result name.
        if not settlement:
            return None

    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])

    except (KeyError, ValueError, TypeError):
        return None

    # Approximate Philippine geographic bounds.
    if not (
        4.0 <= latitude <= 22.0
        and 116.0 <= longitude <= 128.0
    ):
        return None

    region = (
        address.get("state")
        or address.get("region")
        or address.get("province")
        or "Philippines"
    )

    province = (
        address.get("province")
        or address.get("county")
        or ""
    )

    return {
        "name": (
            settlement
            or result_name
            or requested_name
        ),
        "region": region,
        "admin1": region,
        "province": province,
        "country": "Philippines",
        "latitude": latitude,
        "longitude": longitude,
        "display_name": result.get(
            "display_name",
            requested_name
        ),
    }


# ==========================================
# SEARCH PHILIPPINE CITY
# ==========================================

def find_ph_city(city_name):

    if not isinstance(city_name, str):
        return None

    city_name = " ".join(
        city_name.strip().split()
    )

    if not (2 <= len(city_name) <= 100):
        return None

    # Allow input such as:
    # "Iligan City, Lanao del Norte"
    parts = [
        part.strip()
        for part in city_name.split(",")
        if part.strip()
    ]

    if not parts:
        return None

    requested_city = parts[0]

    if not (2 <= len(requested_city) <= 100):
        return None

    normalized = normalize_city_name(
        requested_city
    )

    # Cache key v3 intentionally invalidates
    # results from the previous broken lookup.
    city_hash = hashlib.sha256(
        city_name.casefold().encode("utf-8")
    ).hexdigest()

    cache_key = (
        f"skyaware:nominatim:ph:v3:{city_hash}"
    )

    cached = cache.get(cache_key)

    if cached is not None:
        return cached.get("city")

    # First: structured city lookup.
    # Second: more specific free-text lookup.
    queries = [
        {
            "city": requested_city,
        },
        {
            "q": (
                city_name + ", Philippines"
                if "philippines" not in city_name.casefold()
                else city_name
            ),
        },
    ]

    service_error = None

    for query in queries:

        try:
            results = request_nominatim(query)

        except requests.RequestException as exc:
            service_error = exc
            break

        for result in results:

            city = get_matching_city(
                result,
                requested_city
            )

            if city is None:
                continue

            # If a province was supplied,
            # prefer a result that agrees with it.
            # The final result still needs an
            # exact city-name match.
            if len(parts) > 1:

                expected_province = (
                    normalize_city_name(parts[1])
                )

                actual_location = normalize_city_name(
                    " ".join([
                        str(city.get("province", "")),
                        str(city.get("region", "")),
                        str(
                            city.get(
                                "display_name",
                                ""
                            )
                        ),
                    ])
                )

                if (
                    expected_province
                    and expected_province
                    not in actual_location
                ):
                    continue

            cache.set(
                cache_key,
                {"city": city},
                CACHE_DURATION
            )

            return city

    # Safe reference fallback for Iligan.
    # Never substitute another city.
    if normalized == "iligan":

        city = ILIGAN_REFERENCE.copy()

        cache.set(
            cache_key,
            {"city": city},
            CACHE_DURATION
        )

        return city

    # If the provider is unavailable, let the
    # existing views show their connection error.
    if service_error is not None:
        raise service_error

    # Do not return a different city.
    cache.set(
        cache_key,
        {"city": None},
        3600
    )

    return None
