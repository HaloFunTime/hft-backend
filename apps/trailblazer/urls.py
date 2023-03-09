from django.urls import path

from apps.trailblazer import views

urlpatterns = [
    path(
        "seasonal-role-check",
        views.TrailblazerSeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
]
