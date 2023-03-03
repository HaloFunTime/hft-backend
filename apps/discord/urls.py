from django.urls import path

from apps.discord import views

urlpatterns = [
    path(
        "ranked-role-check",
        views.RankedRoleCheckView.as_view(),
        name="ranked-role-check",
    ),
]
