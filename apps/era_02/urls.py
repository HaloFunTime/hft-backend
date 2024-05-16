from django.urls import path

from apps.era_02 import views

urlpatterns = [
    path(
        "check-player-games",
        views.CheckPlayerGames.as_view(),
        name="check-player-games",
    ),
    path("save-mvt", views.SaveMVT.as_view(), name="save-mvt"),
]
