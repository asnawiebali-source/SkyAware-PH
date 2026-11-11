
from django import forms

from .models import SavedLocation


class SavedLocationForm(forms.ModelForm):

    class Meta:
        model = SavedLocation

        fields = [
            "city",
            "province",
            "country",
        ]

        labels = {
            "city": "City / Municipality",
            "province": "Province",
            "country": "Country",
        }

        widgets = {
            "city": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Search or select a Philippine city",
                    "autocomplete": "off",
                    "list": "philippineCityList",
                    "maxlength": "100",
                }
            ),

            "province": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Automatically filled when available",
                    "maxlength": "100",
                }
            ),

            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "readonly": "readonly",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if not self.is_bound and not self.instance.pk:
            self.fields["country"].initial = "Philippines"

        self.fields["city"].required = True
        self.fields["province"].required = False
        self.fields["country"].required = True

    def clean_city(self):

        city = self.cleaned_data.get(
            "city",
            ""
        ).strip()

        city = " ".join(city.split())

        if len(city) < 2:
            raise forms.ValidationError(
                "Please enter a valid city or municipality."
            )

        return city

    def clean_province(self):

        province = self.cleaned_data.get(
            "province",
            ""
        ).strip()

        return " ".join(province.split())

    def clean_country(self):

        # SkyAware PH currently supports
        # Philippine locations only.
        return "Philippines"
