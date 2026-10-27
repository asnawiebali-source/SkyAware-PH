
from django.contrib import admin
from .models import SavedLocation


@admin.register(SavedLocation)
class SavedLocationAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'city',
        'province',
        'country',
        'user',
        'created_at',
    )

    search_fields = (
        'city',
        'province',
        'country',
        'user__username',
    )

    list_filter = (
        'country',
        'created_at',
    )

    ordering = ('-created_at',)

    readonly_fields = ('created_at',)

    list_per_page = 20
