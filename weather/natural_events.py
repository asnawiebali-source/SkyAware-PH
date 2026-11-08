
import requests

from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone


NASA_API_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"

CATEGORIES = {
    "all": "All Categories",
    "severeStorms": "Severe Storms",
    "wildfires": "Wildfires",
    "volcanoes": "Volcanoes",
    "landslides": "Landslides",
    "floods": "Floods",
    "earthquakes": "Earthquakes",
}

PERIODS = (30, 90, 180, 365)


# =========================================
# SAFE EXTERNAL URL
# =========================================

def safe_url(url):
    if isinstance(url, str) and url.startswith(
        ("https://", "http://")
    ):
        return url

    return None


# =========================================
# FORMAT NASA EVENT
# =========================================

def format_event(item):
    if not isinstance(item, dict):
        return None

    categories = item.get("categories") or []
    geometries = item.get("geometry") or []
    sources = item.get("sources") or []

    if not isinstance(categories, list):
        categories = []

    if not isinstance(geometries, list):
        geometries = []

    if not isinstance(sources, list):
        sources = []

    # Category names
    category_names = [
        category.get("title", "Other")
        for category in categories
        if isinstance(category, dict)
    ]

    category_text = (
        ", ".join(category_names)
        if category_names
        else "Other"
    )

    # Event icon
    category_lower = category_text.lower()

    if "storm" in category_lower:
        icon = "bi-cloud-lightning-rain"
    elif "wildfire" in category_lower:
        icon = "bi-fire"
    elif "volcano" in category_lower:
        icon = "bi-triangle-fill"
    elif "flood" in category_lower:
        icon = "bi-water"
    elif "earthquake" in category_lower:
        icon = "bi-activity"
    elif "landslide" in category_lower:
        icon = "bi-exclamation-triangle"
    else:
        icon = "bi-globe-americas"

    # Latest reported geometry
    valid_geometries = [
        geometry
        for geometry in geometries
        if isinstance(geometry, dict)
    ]

    valid_geometries.sort(
        key=lambda geometry: geometry.get("date") or ""
    )

    latest = (
        valid_geometries[-1]
        if valid_geometries
        else {}
    )

    event_date = latest.get("date") or ""

    latitude = None
    longitude = None

    # NASA coordinates are [longitude, latitude].
    # Only use Point geometry for a precise marker.
    coordinates = latest.get("coordinates")

    if (
        latest.get("type") == "Point"
        and isinstance(coordinates, (list, tuple))
        and len(coordinates) >= 2
    ):
        try:
            longitude = float(coordinates[0])
            latitude = float(coordinates[1])

            if not (
                -180 <= longitude <= 180
                and -90 <= latitude <= 90
            ):
                longitude = None
                latitude = None

        except (ValueError, TypeError):
            longitude = None
            latitude = None

    # Event source
    source_url = None
    source_name = "Event Source"

    for source in sources:
        if not isinstance(source, dict):
            continue

        url = safe_url(source.get("url"))

        if url:
            source_url = url
            source_name = source.get("id") or "Event Source"
            break

    return {
        "title": item.get("title") or "Unnamed Natural Event",
        "description": item.get("description") or "",
        "category": category_text,
        "icon": icon,
        "date": event_date[:10] if event_date else "Not Available",
        "date_raw": event_date,
        "status": "Closed" if item.get("closed") else "Open",
        "latitude": latitude,
        "longitude": longitude,
        "source_url": source_url,
        "source_name": source_name,
        "event_url": safe_url(item.get("link")),
    }


# =========================================
# NASA NATURAL EVENTS VIEW
# =========================================

def natural_events_view(request):

    scope = request.GET.get("scope", "world")
    category = request.GET.get("category", "all")
    status = request.GET.get("status", "all")

    try:
        days = int(request.GET.get("days", "90"))
    except (ValueError, TypeError):
        days = 90

    # Validate user-selected filters
    if scope not in ("world", "ph"):
        scope = "world"

    if category not in CATEGORIES:
        category = "all"

    if status not in ("all", "open", "closed"):
        status = "all"

    if days not in PERIODS:
        days = 90

    # NASA EONET query parameters
    params = {
        "status": status,
        "days": days,
        "limit": 200,
    }

    if category != "all":
        params["category"] = category

    if scope == "ph":
        # Bounding box:
        # west, north, east, south
        params["bbox"] = "116,22,127,4"

    cache_key = (
        f"skyaware:nasa-v4:"
        f"{scope}:{category}:{status}:{days}"
    )

    cached = cache.get(cache_key)

    events = []
    retrieved_at = None
    error = None

    if cached is not None:

        events = cached["events"]
        retrieved_at = cached["retrieved_at"]

    else:

        try:
            response = requests.get(
                NASA_API_URL,
                params=params,
                timeout=20,
                headers={
                    "User-Agent": "SkyAwarePH-EducationalProject/1.0",
                    "Accept": "application/json",
                },
            )

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                raise ValueError("Invalid NASA response.")

            raw_events = data.get("events")

            if not isinstance(raw_events, list):
                raise ValueError("Missing NASA events.")

            for item in raw_events:
                event = format_event(item)

                if event:
                    events.append(event)

            # Latest listed events first
            events.sort(
                key=lambda event: event["date_raw"],
                reverse=True,
            )

            retrieved_at = timezone.localtime()

            # Cache successful API results for 15 minutes
            cache.set(
                cache_key,
                {
                    "events": events,
                    "retrieved_at": retrieved_at,
                },
                900,
            )

        except requests.Timeout:
            error = (
                "NASA EONET is taking too long to respond. "
                "Please try again."
            )

        except requests.RequestException:
            error = (
                "Unable to connect to NASA EONET. "
                "Please check your internet connection."
            )

        except (ValueError, KeyError, TypeError):
            error = (
                "NASA EONET returned unexpected data. "
                "Please try again later."
            )

    context = {
        "events": events,
        "event_count": len(events),
        "scope": scope,
        "category": category,
        "status": status,
        "days": days,
        "categories": CATEGORIES,
        "retrieved_at": retrieved_at,
        "error": error,
    }

    return render(
        request,
        "weather/natural_events.html",
        context,
    )
