from django.urls import path

from apps.trailblazer import views

urlpatterns = [
    path(
        "seasonal-role-check",
        views.TrailblazerSeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
    path(
        "scout-progress",
        views.TrailblazerScoutProgressView.as_view(),
        name="scout-progress",
    ),
]
