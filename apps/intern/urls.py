from django.urls import path

from apps.intern import views

urlpatterns = [
    path("random-chatter", views.RandomInternChatter.as_view(), name="random-chatter"),
    path("pause-chatter", views.PauseInternChatter.as_view(), name="pause-chatter"),
]
