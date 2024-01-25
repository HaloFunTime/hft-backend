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
        "random-hike-queue-quip",
        views.RandomInternHikeQueueQuip.as_view(),
        name="random-hike-queue-quip",
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
        "random-pathfinder-prodigy-demotion-quip",
        views.RandomInternPathfinderProdigyDemotionQuip.as_view(),
        name="random-pathfinder-prodigy-demotion-quip",
    ),
    path(
        "random-pathfinder-prodigy-promotion-quip",
        views.RandomInternPathfinderProdigyPromotionQuip.as_view(),
        name="random-pathfinder-prodigy-promotion-quip",
    ),
    path(
        "random-plus-rep-quip",
        views.RandomInternPlusRepQuip.as_view(),
        name="random-plus-rep-quip",
    ),
    path(
        "random-trailblazer-titan-demotion-quip",
        views.RandomInternTrailblazerTitanDemotionQuip.as_view(),
        name="random-trailblazer-titan-demotion-quip",
    ),
    path(
        "random-trailblazer-titan-promotion-quip",
        views.RandomInternTrailblazerTitanPromotionQuip.as_view(),
        name="random-trailblazer-titan-promotion-quip",
    ),
]
