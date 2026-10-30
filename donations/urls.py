
from django.urls import path

from . import views

urlpatterns = [
    path(
        "donate/",
        views.donate,
        name="donate",
    ),
    path(
        "donate/create/",
        views.create_donation,
        name="create_donation",
    ),
    path(
        "donate/result/<int:pk>/",
        views.donation_result,
        name="donation_result",
    ),
    path(
        "donations/history/",
        views.donation_history,
        name="donation_history",
    ),
]
