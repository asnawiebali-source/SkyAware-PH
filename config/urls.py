
from django.contrib import admin
from django.urls import path, include

from weather.views import home


urlpatterns = [

    # Django Admin Panel
    path(
        'admin/',
        admin.site.urls
    ),

    # Authentication: Register, Login, Logout
    path(
        'accounts/',
        include('accounts.urls')
    ),

    # User Dashboard
    path(
        'dashboard/',
        include('dashboard.urls')
    ),

    # Homepage
    path(
        '',
        home,
        name='home'
    ),

    # Weather API and Saved Locations CRUD
    path(
        '',
        include('weather.urls')
    ),

]
