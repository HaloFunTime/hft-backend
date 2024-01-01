from django.urls import path

from apps.discord import views

urlpatterns = [
    path(
        "csr-snapshot",
        views.CSRSnapshotView.as_view(),
        name="csr-snapshot",
    ),
    path(
        "lfg-thread-help-prompt",
        views.LFGThreadHelpPromptView.as_view(),
        name="lfg-thread-help-prompt",
    ),
    path(
        "ranked-role-check",
        views.RankedRoleCheckView.as_view(),
        name="ranked-role-check",
    ),
]
