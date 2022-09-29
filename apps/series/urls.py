from django.urls import path

from apps.series import views

urlpatterns = [
    path("", views.Series.as_view(), name="series"),
    path("<str:id>/bo3", views.SeriesBo3.as_view(), name="series-bo3"),
    path("<str:id>/bo5", views.SeriesBo5.as_view(), name="series-bo5"),
    path("<str:id>/bo7", views.SeriesBo7.as_view(), name="series-bo7"),
]
