from django.urls import path

from apps.pathfinder import views

urlpatterns = [
    path("change-beans", views.ChangeBeansView.as_view(), name="change-beans"),
    path("check-beans", views.CheckBeansView.as_view(), name="check-beans"),
    path(
        "dynamo-progress",
        views.PathfinderDynamoProgressView.as_view(),
        name="dynamo-progress",
    ),
    path("hike-complete", views.HikeCompleteView.as_view(), name="hike-complete"),
    path("hike-queue", views.HikeQueueView.as_view(), name="hike-queue"),
    path("hike-submission", views.HikeSubmissionView.as_view(), name="hike-submission"),
    path("popular-files", views.PopularFilesView.as_view(), name="popular-files"),
    path(
        "seasonal-role-check",
        views.PathfinderSeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
    path(
        "testing-lfg-post",
        views.PathfinderTestingLFGPostView.as_view(),
        name="waywo-post",
    ),
    path(
        "waywo-comment",
        views.PathfinderWAYWOCommentView.as_view(),
        name="waywo-comment",
    ),
    path(
        "waywo-post",
        views.PathfinderWAYWOPostView.as_view(),
        name="waywo-post",
    ),
    path("weekly-recap", views.WeeklyRecapView.as_view(), name="weekly-recap"),
]
