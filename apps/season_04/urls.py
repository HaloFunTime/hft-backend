from django.urls import path

from apps.season_04 import views

urlpatterns = [
    path("check-stamps", views.CheckStampsView.as_view(), name="check-stamps"),
    path("save-earner", views.SaveEarnerView.as_view(), name="save-earner"),
]
