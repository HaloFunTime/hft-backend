from django.urls import path

from apps.pathfinder import views

urlpatterns = [
    path("hike-submission", views.HikeSubmissionView.as_view(), name="hike-submission"),
    path(
        "seasonal-role-check",
        views.SeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
]
