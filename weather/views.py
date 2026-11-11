
import logging
import requests

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import SavedLocation
from .forms import SavedLocationForm

# Nominatim City Search
from integrations.nominatim import find_ph_city

# Open-Meteo Weather API
from integrations.open_meteo import get_weather

# USGS Earthquake API
from integrations.usgs_earthquake import get_recent_earthquakes

# Open-Meteo Air Quality API
from integrations.air_quality import get_air_quality

# Groq AI
from integrations.groq_ai import (
    ask_groq,
    GroqConfigurationError,
    GroqServiceError,
)


# ==========================================
# LOGGING
# ==========================================

logger = logging.getLogger(__name__)


# ==========================================
# HOMEPAGE
# ==========================================

def home(request):
    return render(request, "home.html")


# ==========================================
# WEATHER FORECAST
# NOMINATIM + OPEN-METEO
# ==========================================

@login_required
def weather_forecast(request):

    city_name = request.GET.get(
        "city",
        "Iligan City",
    ).strip()

    city = None
    weather_data = None
    error = None

    if not city_name:
        error = "Please enter a city name."

    elif len(city_name) > 100:
        error = "City name is too long."

    else:
        try:
            # STEP 1: Find the city using Nominatim
            city = find_ph_city(city_name)

            if city:

                # STEP 2: Retrieve weather from Open-Meteo
                weather_data = get_weather(
                    city["latitude"],
                    city["longitude"],
                )

                if not weather_data:
                    logger.warning(
                        "Open-Meteo returned no weather data "
                        "for city=%s latitude=%s longitude=%s",
                        city_name,
                        city["latitude"],
                        city["longitude"],
                    )

                    error = (
                        "Weather data is currently "
                        "unavailable for this location."
                    )

            else:
                logger.warning(
                    "Nominatim returned no city for query=%s",
                    city_name,
                )

                error = (
                    "City not found in the Philippines. "
                    "Please try another city."
                )

        except requests.RequestException as exc:

            # Shows the actual connection or HTTP error
            # in Render application logs.
            logger.exception(
                "Weather forecast request failed "
                "for city=%s: %s",
                city_name,
                exc,
            )

            error = (
                "Unable to connect to the location "
                "or weather service. Please try again."
            )

        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            # Shows parsing and data processing errors.
            logger.exception(
                "Weather data processing failed "
                "for city=%s: %s",
                city_name,
                exc,
            )

            error = (
                "Weather information is temporarily "
                "unavailable. Please try again."
            )

    return render(
        request,
        "weather/forecast.html",
        {
            "city_name": city_name,
            "city": city,
            "weather_data": weather_data,
            "error": error,
        },
    )


# ==========================================
# EARTHQUAKE UPDATES
# USGS EARTHQUAKE API
# ==========================================

@login_required
def earthquake_updates(request):

    earthquake_data = None
    error = None

    try:
        earthquake_data = get_recent_earthquakes(
            days=7,
            min_magnitude=2.5,
        )

    except requests.RequestException as exc:

        logger.exception(
            "USGS Earthquake API request failed: %s",
            exc,
        )

        error = (
            "Unable to connect to the USGS "
            "earthquake service. Please try later."
        )

    except (
        ValueError,
        KeyError,
        TypeError,
        OverflowError,
    ) as exc:

        logger.exception(
            "Earthquake data processing failed: %s",
            exc,
        )

        error = (
            "Earthquake data is temporarily "
            "unavailable. Please try again later."
        )

    return render(
        request,
        "weather/earthquakes.html",
        {
            "earthquake_data": earthquake_data,
            "error": error,
        },
    )


# ==========================================
# AIR QUALITY
# NOMINATIM + OPEN-METEO AIR QUALITY
# ==========================================

@login_required
def air_quality_view(request):

    city_name = request.GET.get(
        "city",
        "Iligan City",
    ).strip()

    city = None
    air_quality_data = None
    error = None

    if not city_name:
        error = "Please enter a city name."

    elif len(city_name) > 100:
        error = "City name is too long."

    else:
        try:
            # STEP 1: Find city using Nominatim
            city = find_ph_city(city_name)

            if city:

                # STEP 2: Get air quality data
                air_quality_data = get_air_quality(
                    city["latitude"],
                    city["longitude"],
                )

                if not air_quality_data:

                    logger.warning(
                        "Air Quality API returned no data "
                        "for city=%s",
                        city_name,
                    )

                    error = (
                        "Air quality data is currently "
                        "unavailable for this location."
                    )

            else:
                error = (
                    "City not found in the Philippines. "
                    "Please try another city."
                )

        except requests.RequestException as exc:

            logger.exception(
                "Air Quality API request failed "
                "for city=%s: %s",
                city_name,
                exc,
            )

            error = (
                "Unable to connect to the location "
                "or air quality service. "
                "Please try again."
            )

        except (
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as exc:

            logger.exception(
                "Air quality processing failed "
                "for city=%s: %s",
                city_name,
                exc,
            )

            error = (
                "Air quality information is temporarily "
                "unavailable. Please try again later."
            )

    return render(
        request,
        "weather/air_quality.html",
        {
            "city_name": city_name,
            "city": city,
            "air_quality_data": air_quality_data,
            "error": error,
        },
    )


# ==========================================
# GROQ AI SAFETY ASSISTANT
# ==========================================

@login_required
@require_http_methods(["GET", "POST"])
def ai_assistant(request):

    question = ""
    answer = None
    error = None

    if request.method == "POST":

        question = request.POST.get(
            "question",
            "",
        ).strip()

        if not question:
            error = "Please enter your question."

        elif len(question) > 1000:
            error = (
                "Your question is too long. "
                "Please use 1000 characters or fewer."
            )

        else:
            try:
                answer = ask_groq(question)

            except GroqConfigurationError:
                error = (
                    "Groq API is not configured. "
                    "Please contact the administrator."
                )

            except GroqServiceError as exc:
                logger.warning(
                    "Groq AI service failed: %s",
                    exc,
                )

                error = str(exc)

    return render(
        request,
        "weather/ai_assistant.html",
        {
            "question": question,
            "answer": answer,
            "error": error,
        },
    )


# ==========================================
# SAVED LOCATIONS - READ
# ==========================================

@login_required
def saved_locations(request):

    locations = SavedLocation.objects.filter(
        user=request.user,
    )

    return render(
        request,
        "weather/saved_locations.html",
        {
            "locations": locations,
        },
    )


# ==========================================
# SAVED LOCATIONS - CREATE
# ==========================================

@login_required
def add_location(request):

    if request.method == "POST":

        form = SavedLocationForm(request.POST)

        if form.is_valid():

            location = form.save(commit=False)

            location.user = request.user
            location.save()

            messages.success(
                request,
                "Location added successfully!",
            )

            return redirect("saved_locations")

    else:
        form = SavedLocationForm()

    return render(
        request,
        "weather/location_form.html",
        {
            "form": form,
            "title": "Add Location",
        },
    )


# ==========================================
# SAVED LOCATIONS - UPDATE
# ==========================================

@login_required
def edit_location(request, pk):

    location = get_object_or_404(
        SavedLocation,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":

        form = SavedLocationForm(
            request.POST,
            instance=location,
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Location updated successfully!",
            )

            return redirect("saved_locations")

    else:
        form = SavedLocationForm(instance=location)

    return render(
        request,
        "weather/location_form.html",
        {
            "form": form,
            "title": "Edit Location",
        },
    )


# ==========================================
# SAVED LOCATIONS - DELETE
# ==========================================

@login_required
def delete_location(request, pk):

    location = get_object_or_404(
        SavedLocation,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":

        location.delete()

        messages.success(
            request,
            "Location deleted successfully!",
        )

        return redirect("saved_locations")

    return render(
        request,
        "weather/delete_location.html",
        {
            "location": location,
        },
    )
