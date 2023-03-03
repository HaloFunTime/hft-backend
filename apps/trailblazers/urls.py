from django.urls import path

from apps.trailblazers import views

urlpatterns = [
    path(
        "seasonal-role-check",
        views.SeasonalRoleCheckView.as_view(),
        name="seasonal-role-check",
    ),
]
