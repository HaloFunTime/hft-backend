from django.urls import path

from apps.showcase import views

urlpatterns = [
    path("add-file", views.AddFileView.as_view(), name="add-file"),
    path("check-showcase", views.CheckShowcaseView.as_view(), name="check-showcase"),
    path("remove-file", views.RemoveFileView.as_view(), name="remove-file"),
]
