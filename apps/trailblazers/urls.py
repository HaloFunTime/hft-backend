from django.urls import path

from apps.trailblazers import views

urlpatterns = [
    path(
        "trailblazer-role-check",
        views.TrailblazerRoleCheckView.as_view(),
        name="trailblazer-role-check",
    ),
    # path("pathfinder-role-check", views.PathfinderRoleCheckView.as_view(), name="pathfinder-role-check"),
]
