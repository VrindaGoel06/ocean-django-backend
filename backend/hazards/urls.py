# common/urls.py
from django.urls import path
from .views import UserReportCreateView

urlpatterns = [
    path("user-reports/", UserReportCreateView.as_view(), name="user-report-create"),
]
