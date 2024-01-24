from django.urls import path

from apps.era_01 import views

urlpatterns = [
    path("check-bingo-card", views.CheckBingoCard.as_view(), name="check-bingo-card"),
    path(
        "check-participant-games",
        views.CheckParticipantGames.as_view(),
        name="check-participant-games",
    ),
    path("join-challenge", views.JoinChallenge.as_view(), name="join-challenge"),
    path("save-buff", views.SaveBuff.as_view(), name="save-buff"),
]
