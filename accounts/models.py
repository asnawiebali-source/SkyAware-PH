
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator


ph_contact_validator = RegexValidator(
    regex=r"^09[0-9]{9}$",
    message="Enter a valid 11-digit Philippine contact number (09XXXXXXXXX).",
)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skyaware_profile",
    )

    contact_number = models.CharField(
        max_length=11,
        blank=True,
        validators=[ph_contact_validator],
    )

    def __str__(self):
        return f"{self.user.username} - Profile"
