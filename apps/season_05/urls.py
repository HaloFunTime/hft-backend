from django.urls import path

from apps.season_05 import views

urlpatterns = [
    path("check-domains", views.CheckDomainsView.as_view(), name="check-domains"),
    path("check-teams", views.CheckTeamsView.as_view(), name="check-teams"),
    path("join-challenge", views.JoinChallengeView.as_view(), name="join-challenge"),
    path(
        "process-reassignments",
        views.ProcessReassignmentsView.as_view(),
        name="process-reassignments",
    ),
    path("save-master", views.SaveMasterView.as_view(), name="save-master"),
]
