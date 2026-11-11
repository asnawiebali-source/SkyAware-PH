
from django.contrib import messages

from django.contrib.auth import (
    update_session_auth_hash,
)

from django.contrib.auth.decorators import login_required

from django.contrib.auth.forms import PasswordChangeForm

from django.shortcuts import render, redirect

from django.views.decorators.http import require_http_methods

from .forms import (
    RegisterForm,
    ProfileUpdateForm,
)

from .models import UserProfile


# ==========================================
# REGISTER USER
# ==========================================

@require_http_methods(["GET", "POST"])
def register_view(request):

    # Already logged-in users go to dashboard.
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

            # Save the account and contact number.
            form.save()

            # Do not automatically log in.
            # User must sign in manually.

            messages.success(
                request,
                "Account created successfully! "
                "Please log in using your username "
                "and password."
            )

            # Redirect to login page.
            return redirect("login")

    else:

        form = RegisterForm()

    return render(
        request,
        "accounts/register.html",
        {
            "form": form,
        }
    )


# ==========================================
# USER PROFILE SETTINGS
# ==========================================

@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):

    # Create profile for existing users
    # who do not have one yet.
    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    profile_form = ProfileUpdateForm(
        instance=request.user,
        profile=profile,
    )

    password_form = PasswordChangeForm(
        user=request.user,
    )

    for name, field in password_form.fields.items():

        field.widget.attrs["class"] = "form-control"

        field.widget.attrs["autocomplete"] = (
            "current-password"
            if name == "old_password"
            else "new-password"
        )

    if request.method == "POST":

        action = request.POST.get("action")

        # ==================================
        # UPDATE PROFILE INFORMATION
        # ==================================

        if action == "update_profile":

            profile_form = ProfileUpdateForm(
                request.POST,
                instance=request.user,
                profile=profile,
            )

            if profile_form.is_valid():

                profile_form.save()

                messages.success(
                    request,
                    "Your profile has been "
                    "updated successfully."
                )

                return redirect("profile")

        # ==================================
        # CHANGE PASSWORD
        # ==================================

        elif action == "change_password":

            password_form = PasswordChangeForm(
                user=request.user,
                data=request.POST,
            )

            for name, field in password_form.fields.items():

                field.widget.attrs["class"] = "form-control"

                field.widget.attrs["autocomplete"] = (
                    "current-password"
                    if name == "old_password"
                    else "new-password"
                )

            if password_form.is_valid():

                user = password_form.save()

                # Keep user logged in after
                # changing their password.
                update_session_auth_hash(
                    request,
                    user
                )

                messages.success(
                    request,
                    "Your password has been "
                    "changed successfully."
                )

                return redirect("profile")

        else:

            messages.error(
                request,
                "Invalid profile action."
            )

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile,
            "profile_form": profile_form,
            "password_form": password_form,
        }
    )
