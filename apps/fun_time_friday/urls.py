from django.urls import path

from apps.fun_time_friday import views

urlpatterns = [
    path("report", views.ReportView.as_view(), name="report"),
    path("voice-connect", views.VoiceConnectView.as_view(), name="voice-connect"),
    path(
        "voice-disconnect", views.VoiceDisconnectView.as_view(), name="voice-disconnect"
    ),
]
