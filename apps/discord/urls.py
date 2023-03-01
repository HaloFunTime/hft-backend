from django.urls import path

from apps.discord import views

urlpatterns = [
    path(
        "ranked-role-check",
        views.RankedRoleCheckView.as_view(),
        name="ranked-role-check",
    ),
    # path("trailblazer-role-check", views.TrailblazerRoleCheckView.as_view(), name="trailblazer-role-check"),
    # path("pathfinder-role-check", views.PathfinderRoleCheckView.as_view(), name="pathfinder-role-check"),
]
