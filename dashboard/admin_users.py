
"""
SkyAware PH - Custom Admin User Management

Features:
    - View registered regular users
    - Search users by username, name or email
    - Edit user account information
    - Reset regular-user passwords

The interface does not support:
    - Role changes
    - Account activation or deactivation
    - Modifying administrator accounts
"""

import logging

from django import forms
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_http_methods


logger = logging.getLogger(__name__)

User = get_user_model()


# ==========================================
# EDIT ACCOUNT INFORMATION FORM
# ==========================================

class AccountDetailsForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "autocomplete": "off",
                }
            ),
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }


# ==========================================
# REGULAR USERS ONLY
# ==========================================

def regular_users():
    return User.objects.filter(
        is_staff=False,
        is_superuser=False,
    )


# ==========================================
# ADMIN - VIEW AND SEARCH USERS
# ==========================================

@staff_member_required(login_url="login")
@require_http_methods(["GET"])
def admin_users_view(request):

    query = request.GET.get("q", "").strip()[:100]

    all_users = regular_users()

    accounts = all_users.order_by(
        "-date_joined",
        "-pk",
    )

    # Filter accounts using search input.
    if query:

        accounts = accounts.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
        )

    # Show 10 user accounts per page.
    paginator = Paginator(accounts, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "accounts": page_obj,
        "page_obj": page_obj,
        "query": query,
        "total_users": all_users.count(),
    }

    return render(
        request,
        "dashboard/admin_users.html",
        context,
    )


# ==========================================
# ADMIN - MANAGE A USER
# ==========================================

@staff_member_required(login_url="login")
@require_http_methods(["GET", "POST"])
def admin_user_detail_view(request, pk):

    # Do not allow administrator accounts
    # to be modified from this page.
    account = get_object_or_404(
        regular_users(),
        pk=pk,
    )

    # Edit information form.
    details_form = AccountDetailsForm(
        instance=account
    )

    # Secure Django password reset form.
    password_form = SetPasswordForm(
        account
    )

    # ======================================
    # PROCESS FORM SUBMISSION
    # ======================================

    if request.method == "POST":

        action = request.POST.get(
            "action",
            ""
        )

        # ----------------------------------
        # EDIT USER INFORMATION
        # ----------------------------------

        if action == "save_details":

            details_form = AccountDetailsForm(
                request.POST,
                instance=account,
            )

            if details_form.is_valid():

                details_form.save()

                logger.info(
                    "Admin %s updated user %s",
                    request.user.pk,
                    account.pk,
                )

                messages.success(
                    request,
                    "User information updated successfully.",
                )

                return redirect(
                    "admin_user_detail",
                    pk=account.pk,
                )

        # ----------------------------------
        # RESET USER PASSWORD
        # ----------------------------------

        elif action == "reset_password":

            password_form = SetPasswordForm(
                account,
                request.POST,
            )

            if password_form.is_valid():

                # Django validates and hashes
                # the password before saving.
                password_form.save()

                # Never log the actual password.
                logger.info(
                    "Admin %s reset password for user %s",
                    request.user.pk,
                    account.pk,
                )

                messages.success(
                    request,
                    "User password reset successfully.",
                )

                return redirect(
                    "admin_user_detail",
                    pk=account.pk,
                )

        else:

            messages.error(
                request,
                "Invalid user management action.",
            )

    # ======================================
    # STYLE PASSWORD FORM FIELDS
    # ======================================

    for field in password_form.fields.values():

        field.widget.attrs.update({
            "class": "form-control",
            "autocomplete": "new-password",
        })

    # ======================================
    # RENDER USER MANAGEMENT PAGE
    # ======================================

    context = {
        "account": account,
        "details_form": details_form,
        "password_form": password_form,
    }

    return render(
        request,
        "dashboard/admin_user_detail.html",
        context,
    )
