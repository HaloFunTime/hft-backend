from django.urls import path

from apps.reputation import views

urlpatterns = [
    path("check-rep", views.CheckRep.as_view(), name="check-rep"),
    path("partytimers", views.PartyTimers.as_view(), name="partytimers"),
    path("plus-rep", views.NewPlusRep.as_view(), name="plus-rep"),
    path("top-rep", views.TopRep.as_view(), name="top-rep"),
]
