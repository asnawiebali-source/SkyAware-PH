
import requests

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from integrations.usgs_earthquake import get_recent_earthquakes


# Allowed search periods and magnitudes.
# Restrict user input to supported values.
ALLOWED_DAYS = (1, 7, 14, 30)
ALLOWED_MAGNITUDES = (2.5, 4.0, 6.0)

DEFAULT_DAYS = 7
DEFAULT_MAGNITUDE = 2.5


@login_required
def earthquake_updates(request):
    """
    Show recent Philippine earthquakes from USGS.

    URL examples:
      /earthquakes/
      /earthquakes/?days=14&min_magnitude=2.5
      /earthquakes/?days=30&min_magnitude=4.0
    """

    # Read reporting period safely.
    try:
        days = int(
            request.GET.get("days", DEFAULT_DAYS)
        )
    except (ValueError, TypeError):
        days = DEFAULT_DAYS

    if days not in ALLOWED_DAYS:
        days = DEFAULT_DAYS

    # Read minimum magnitude safely.
    try:
        min_magnitude = float(
            request.GET.get(
                "min_magnitude",
                DEFAULT_MAGNITUDE
            )
        )
    except (ValueError, TypeError):
        min_magnitude = DEFAULT_MAGNITUDE

    if min_magnitude not in ALLOWED_MAGNITUDES:
        min_magnitude = DEFAULT_MAGNITUDE

    earthquake_data = None
    error = None

    try:
        earthquake_data = get_recent_earthquakes(
            days=days,
            min_magnitude=min_magnitude
        )

    except requests.RequestException:
        error = (
            "Unable to connect to the USGS earthquake "
            "service. Please try again later."
        )

    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        OverflowError
    ):
        error = (
            "Earthquake information is temporarily "
            "unavailable. Please try again later."
        )

    context = {
        "earthquake_data": earthquake_data,
        "error": error,
        "selected_days": days,
        "selected_magnitude": min_magnitude,
        "allowed_days": ALLOWED_DAYS,
    }

    return render(
        request,
        "weather/earthquakes.html",
        context
    )
