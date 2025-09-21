from django.contrib import admin
from leaflet.admin import LeafletGeoAdmin
from .models import GeoVideo


@admin.register(GeoVideo)
class GeoVideoAdmin(LeafletGeoAdmin):
    list_display = ("id", "timestamp_utc", "location", "altitude")
