from django.urls import path

from apps.era_03 import views

urlpatterns = [
    path("board-boat", views.BoardBoat.as_view(), name="board-boat"),
    path(
        "check-boat-assignments",
        views.CheckBoatAssignments.as_view(),
        name="check-boat-assignments",
    ),
    path(
        "check-deckhand-games",
        views.CheckDeckhandGames.as_view(),
        name="check-deckhand-games",
    ),
    path(
        "save-boat-captain", views.SaveBoatCaptain.as_view(), name="save-boat-captain"
    ),
]
