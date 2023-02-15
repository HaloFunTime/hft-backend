from django.urls import path

from apps.link import views

urlpatterns = [
    path(
        "discord-and-xbox-live",
        views.LinkDiscordAndXboxLive.as_view(),
        name="discord-and-xbox-live",
    ),
]
