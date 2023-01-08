from django.urls import path

from apps.intern import views

urlpatterns = [
    path("pause-chatter", views.PauseInternChatter.as_view(), name="pause-chatter"),
    path("random-chatter", views.RandomInternChatter.as_view(), name="random-chatter"),
    path(
        "random-helpful-hint",
        views.RandomInternHelpfulHint.as_view(),
        name="helpful-hint",
    ),
]
