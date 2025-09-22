# common/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("reporting", views.render_report, name="report"),
    path("report_submit", views.render_report_submit, name="report_submit"),
]
