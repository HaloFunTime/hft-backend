from django.urls import path

from apps.season_05 import views

urlpatterns = [
    path("join-challenge", views.JoinChallengeView.as_view(), name="join-challenge"),
    path("save-master", views.SaveMasterView.as_view(), name="save-master"),
]
