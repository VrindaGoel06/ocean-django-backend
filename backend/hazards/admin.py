from django.contrib import admin
from .models import UserReport


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "user_submit_type",
        "type",
        "action_status",
        "severity",
        "confidence",
        "created_at",
        "user",
        "updated_at",
    )
