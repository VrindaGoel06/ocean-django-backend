# common/urls.py
from django.urls import path
from .views import render_map

urlpatterns = [
    path("map/", render_map, name="map"),
]
