
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from .models import UserProfile, ph_contact_validator


User = get_user_model()


# ==========================================
# CONTACT NUMBER FIELD
# ==========================================

class ContactNumberField(forms.CharField):

    def __init__(self, *args, **kwargs):

        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 11)
        kwargs.setdefault(
            "label",
            "Contact Number (Optional)"
        )

        kwargs.setdefault(
            "help_text",
            "Philippine mobile number (09XXXXXXXXX)."
        )

        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "placeholder": "Contact Number",
                    "inputmode": "numeric",
                    "autocomplete": "tel",
                    "maxlength": "11",
                    "pattern": "09[0-9]{9}",
                }
            )
        )

        super().__init__(*args, **kwargs)

        self.validators.append(ph_contact_validator)


# ==========================================
# REGISTRATION FORM
# ==========================================

class RegisterForm(UserCreationForm):

    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First Name",
    )

    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last Name",
    )

    email = forms.EmailField(
        required=True,
        label="Email Address",
    )

    contact_number = ContactNumberField()

    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "username",
            "email",
            "contact_number",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        self.fields["first_name"].widget.attrs.update({
            "placeholder": "Enter your first name",
            "autocomplete": "given-name",
        })

        self.fields["last_name"].widget.attrs.update({
            "placeholder": "Enter your last name",
            "autocomplete": "family-name",
        })

        self.fields["username"].widget.attrs.update({
            "placeholder": "Username",
            "autocomplete": "username",
        })

        self.fields["email"].widget.attrs.update({
            "placeholder": "Email Address",
            "autocomplete": "email",
        })

        self.fields["password1"].widget.attrs.update({
            "placeholder": "Create a password",
            "autocomplete": "new-password",
        })

        self.fields["password2"].widget.attrs.update({
            "placeholder": "Confirm your password",
            "autocomplete": "new-password",
        })

    # --------------------------------------
    # VALIDATE EMAIL
    # --------------------------------------

    def clean_email(self):

        email = self.cleaned_data["email"].strip()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    # --------------------------------------
    # SAVE USER AND PROFILE
    # --------------------------------------

    def save(self, commit=True):

        user = super().save(commit=False)

        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        if commit:

            with transaction.atomic():

                user.save()

                UserProfile.objects.create(
                    user=user,
                    contact_number=self.cleaned_data.get(
                        "contact_number", ""
                    ),
                )

        return user


# ==========================================
# PROFILE UPDATE FORM
# ==========================================

class ProfileUpdateForm(forms.ModelForm):

    email = forms.EmailField(
        required=True,
        label="Email Address",
    )

    contact_number = ContactNumberField()

    class Meta:
        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "contact_number",
        ]

        labels = {
            "username": "Username",
            "first_name": "First Name",
            "last_name": "Last Name",
        }

    def __init__(self, *args, **kwargs):

        profile = kwargs.pop("profile", None)

        super().__init__(*args, **kwargs)

        if profile is not None and not self.is_bound:

            self.fields["contact_number"].initial = (
                profile.contact_number
            )

        for name, field in self.fields.items():
            field.widget.attrs["class"] = "form-control"

        self.fields["username"].widget.attrs.update({
            "autocomplete": "username",
        })

        self.fields["first_name"].widget.attrs.update({
            "placeholder": "Enter your first name",
            "autocomplete": "given-name",
        })

        self.fields["last_name"].widget.attrs.update({
            "placeholder": "Enter your last name",
            "autocomplete": "family-name",
        })

        self.fields["email"].widget.attrs.update({
            "placeholder": "you@example.com",
            "autocomplete": "email",
        })

    # --------------------------------------
    # VALIDATE EMAIL
    # --------------------------------------

    def clean_email(self):

        email = self.cleaned_data["email"].strip()

        duplicate = User.objects.filter(
            email__iexact=email
        )

        if self.instance.pk:

            duplicate = duplicate.exclude(
                pk=self.instance.pk
            )

        if duplicate.exists():

            raise forms.ValidationError(
                "This email is already used by another account."
            )

        return email

    # --------------------------------------
    # SAVE PROFILE
    # --------------------------------------

    def save(self, commit=True):

        user = super().save(commit=False)

        if commit:

            with transaction.atomic():

                user.save()

                profile, created = (
                    UserProfile.objects.get_or_create(
                        user=user
                    )
                )

                profile.contact_number = (
                    self.cleaned_data.get(
                        "contact_number", ""
                    )
                )

                profile.full_clean()
                profile.save()

        return user
