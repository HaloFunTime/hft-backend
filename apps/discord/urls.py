from django.urls import path

from apps.discord import views

urlpatterns = [
    path(
        "csr-snapshot",
        views.CSRSnapshotView.as_view(),
        name="csr-snapshot",
    ),
    path(
        "ranked-role-check",
        views.RankedRoleCheckView.as_view(),
        name="ranked-role-check",
    ),
]
