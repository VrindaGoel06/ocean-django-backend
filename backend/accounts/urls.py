from django.urls import path
from . import views

urlpatterns = [
    path("login", views.render_login, name="login"),
    path("signup", views.render_signup, name="signup"),
    path("", views.render_dashboard, name="dashboard"),
    path("gamification", views.render_gamification, name="gamification"),
    path("rewards", views.render_rewards, name="rewards"),
    path("history", views.render_history, name="history"),
    path("test", views.render_test, name="test"),
]
