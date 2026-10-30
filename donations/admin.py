
from django.contrib import admin

from .models import Donation


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "amount",
        "status",
        "created_at",
        "paid_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "user__username",
        "checkout_session_id",
    )
    readonly_fields = (
        "user",
        "amount",
        "status",
        "checkout_session_id",
        "created_at",
        "paid_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
