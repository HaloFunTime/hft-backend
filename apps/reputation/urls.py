from django.urls import path

from apps.reputation import views

urlpatterns = [
    path("plus-rep", views.NewPlusRep.as_view(), name="plus-rep"),
]
