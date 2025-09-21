from django.contrib import admin
from .models import UserReport


@admin.register(UserReport)
class UserReportAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "user_submit_type",
        "action_status",
        "created_at",
        "user",
        "updated_at",
    )
