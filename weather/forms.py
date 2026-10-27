
from django import forms
from .models import SavedLocation


class SavedLocationForm(forms.ModelForm):
    class Meta:
        model = SavedLocation
        fields = ['city', 'province', 'country']

        widgets = {
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Iligan City'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Lanao del Norte'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }
