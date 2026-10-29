
import requests

from django.shortcuts import (
    render,
    redirect,
    get_object_or_404
)

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from .models import SavedLocation
from .forms import SavedLocationForm

from integrations.open_meteo import (
    search_city,
    get_weather
)

from integrations.usgs_earthquake import (
    get_recent_earthquakes
)

from integrations.air_quality import (
    get_air_quality
)

from integrations.groq_ai import (
    ask_groq,
    GroqConfigurationError,
    GroqServiceError
)


# ==========================================
# HOMEPAGE
# ==========================================

def home(request):
    return render(request, "home.html")


# ==========================================
# WEATHER FORECAST
# ==========================================

@login_required
def weather_forecast(request):

    city_name = request.GET.get(
        "city", "Iligan City"
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
            city = search_city(city_name)

            if city:
                weather_data = get_weather(
                    city["latitude"],
                    city["longitude"]
                )
            else:
                error = (
                    "City not found in the Philippines. "
                    "Please try another city."
                )

        except requests.RequestException:
            error = (
                "Unable to connect to the weather "
                "service. Please try again."
            )

        except (ValueError, KeyError, IndexError):
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
        }
    )


# ==========================================
# EARTHQUAKE UPDATES
# ==========================================

@login_required
def earthquake_updates(request):

    earthquake_data = None
    error = None

    try:
        earthquake_data = get_recent_earthquakes(
            days=7,
            min_magnitude=2.5
        )

    except requests.RequestException:
        error = (
            "Unable to connect to the USGS "
            "earthquake service. Please try later."
        )

    except (ValueError, KeyError, TypeError, OverflowError):
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
        }
    )


# ==========================================
# AIR QUALITY
# ==========================================

@login_required
def air_quality_view(request):

    city_name = request.GET.get(
        "city", "Iligan City"
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
            city = search_city(city_name)

            if city:
                air_quality_data = get_air_quality(
                    city["latitude"],
                    city["longitude"]
                )
            else:
                error = (
                    "City not found in the Philippines. "
                    "Please try another city."
                )

        except requests.RequestException:
            error = (
                "Unable to connect to the Air Quality API. "
                "Please try again."
            )

        except (ValueError, KeyError, IndexError, TypeError):
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
        }
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
            "question", ""
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
                error = str(exc)

    return render(
        request,
        "weather/ai_assistant.html",
        {
            "question": question,
            "answer": answer,
            "error": error,
        }
    )


# ==========================================
# SAVED LOCATIONS - READ
# ==========================================

@login_required
def saved_locations(request):

    locations = SavedLocation.objects.filter(
        user=request.user
    )

    return render(
        request,
        "weather/saved_locations.html",
        {
            "locations": locations
        }
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
                "Location added successfully!"
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
        }
    )


# ==========================================
# SAVED LOCATIONS - UPDATE
# ==========================================

@login_required
def edit_location(request, pk):

    location = get_object_or_404(
        SavedLocation,
        pk=pk,
        user=request.user
    )

    if request.method == "POST":

        form = SavedLocationForm(
            request.POST,
            instance=location
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Location updated successfully!"
            )

            return redirect("saved_locations")

    else:
        form = SavedLocationForm(
            instance=location
        )

    return render(
        request,
        "weather/location_form.html",
        {
            "form": form,
            "title": "Edit Location",
        }
    )


# ==========================================
# SAVED LOCATIONS - DELETE
# ==========================================

@login_required
def delete_location(request, pk):

    location = get_object_or_404(
        SavedLocation,
        pk=pk,
        user=request.user
    )

    if request.method == "POST":

        location.delete()

        messages.success(
            request,
            "Location deleted successfully!"
        )

        return redirect("saved_locations")

    return render(
        request,
        "weather/delete_location.html",
        {
            "location": location
        }
    )
