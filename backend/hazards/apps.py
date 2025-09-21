from django.apps import AppConfig


class HazardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hazards"

    def ready(self):
        # Import signals so the receivers register
        from . import signals
