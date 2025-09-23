# common/urls.py
from django.urls import path
from .views import geovideos_geojson

urlpatterns = [
    path("geovideos/", geovideos_geojson, name="geovideos_geojson"),
]
