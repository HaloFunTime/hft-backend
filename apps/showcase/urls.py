from django.urls import path

from apps.showcase import views

urlpatterns = [
    path("check-showcase", views.CheckShowcaseView.as_view(), name="check-showcase"),
]
