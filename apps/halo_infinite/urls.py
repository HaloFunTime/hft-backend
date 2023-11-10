from django.urls import path

from apps.halo_infinite import views

urlpatterns = [
    path("career-rank", views.CareerRankView.as_view(), name="career-rank"),
    path("csr", views.CSRView.as_view(), name="csr"),
    path("recent-games", views.RecentGamesView.as_view(), name="recent-games"),
    path("summary-stats", views.SummaryStatsView.as_view(), name="summary-stats"),
]
