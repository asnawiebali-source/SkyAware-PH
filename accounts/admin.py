
from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "contact_number",
    )

    search_fields = (
        "user__username",
        "user__email",
        "contact_number",
    )

    list_select_related = (
        "user",
    )

    ordering = (
        "user__username",
    )
