from django.urls import path

from apps.halo_infinite import views

urlpatterns = [
    path("csr", views.CSRView.as_view(), name="csr"),
    path("summary-stats", views.SummaryStatsView.as_view(), name="summary-stats"),
]
