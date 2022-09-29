from django.urls import path

from apps.ping import views

urlpatterns = [
    path("", views.Ping.as_view(), name="ping"),
]
