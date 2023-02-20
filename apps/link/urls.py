from django.urls import path

from apps.link import views

urlpatterns = [
    path(
        "discord-to-xbox-live",
        views.DiscordToXboxLive.as_view(),
        name="discord-to-xbox-live",
    ),
]
