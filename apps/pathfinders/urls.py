from django.urls import path

from apps.pathfinders import views

urlpatterns = [
    path(
        "pathfinder-role-check",
        views.PathfinderRoleCheckView.as_view(),
        name="pathfinder-role-check",
    ),
]
