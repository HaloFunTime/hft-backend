from django.urls import path

from apps.pathfinder import views

urlpatterns = [
    path(
        "dynamo-progress",
        views.PathfinderDynamoProgressView.as_view(),
        name="dynamo-progress",
    ),
    path("hike-queue", views.HikeQueueView.as_view(), name="hike-queue"),
    path("hike-submission", views.HikeSubmissionView.as_view(), name="hike-submission"),
    path(
        "seasonal-role-check",
        views.PathfinderSeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
    path(
        "waywo-post",
        views.PathfinderWAYWOPostView.as_view(),
        name="waywo-post",
    ),
]
