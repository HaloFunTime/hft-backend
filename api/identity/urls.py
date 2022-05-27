from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from . import views

urlpatterns = [
    path("identities/", views.IdentityList.as_view()),
    path("identities/<uuid:id>/", views.IdentityDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
