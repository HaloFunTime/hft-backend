from django.urls import path

from apps.intern import views

urlpatterns = [
    path("pause-chatter", views.PauseInternChatter.as_view(), name="pause-chatter"),
    path("random-chatter", views.RandomInternChatter.as_view(), name="random-chatter"),
    path(
        "random-chatter-pause-acceptance-quip",
        views.RandomInternChatterPauseAcceptanceQuip.as_view(),
        name="random-chatter-pause-acceptance-quip",
    ),
    path(
        "random-chatter-pause-denial-quip",
        views.RandomInternChatterPauseDenialQuip.as_view(),
        name="random-chatter-pause-denial-quip",
    ),
    path(
        "random-chatter-pause-reverence-quip",
        views.RandomInternChatterPauseReverenceQuip.as_view(),
        name="random-chatter-pause-reverence-quip",
    ),
    path(
        "random-helpful-hint",
        views.RandomInternHelpfulHint.as_view(),
        name="helpful-hint",
    ),
    path(
        "random-new-here-welcome-quip",
        views.RandomInternNewHereWelcomeQuip.as_view(),
        name="random-new-here-welcome-quip",
    ),
    path(
        "random-new-here-yeet-quip",
        views.RandomInternNewHereYeetQuip.as_view(),
        name="random-new-here-yeet-quip",
    ),
    path(
        "random-passion-report-quip",
        views.RandomInternPassionReportQuip.as_view(),
        name="random-passion-report-quip",
    ),
    path(
        "random-plus-rep-quip",
        views.RandomInternPlusRepQuip.as_view(),
        name="random-plus-rep-quip",
    ),
]
