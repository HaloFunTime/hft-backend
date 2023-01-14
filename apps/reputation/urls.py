from django.urls import path

from apps.reputation import views

urlpatterns = [
    path("check-rep", views.CheckRep.as_view(), name="check-rep"),
    path("plus-rep", views.NewPlusRep.as_view(), name="plus-rep"),
]
