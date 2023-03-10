from django.contrib import admin

from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(FunTimeFridayVoiceConnect)
class FunTimeFridayVoiceConnectAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["connector_discord"]
    list_display = (
        "__str__",
        linkify("connector_discord"),
        "connected_at",
        "channel_name",
        "creator",
    )
    list_filter = (
        "connector_discord",
        "creator",
    )
    fields = (
        "connector_discord",
        "connected_at",
        "channel_id",
        "channel_name",
        "creator",
    )


@admin.register(FunTimeFridayVoiceDisconnect)
class FunTimeFridayVoiceDisconnectAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["disconnector_discord"]
    list_display = (
        "__str__",
        linkify("disconnector_discord"),
        "disconnected_at",
        "channel_name",
        "creator",
    )
    list_filter = (
        "disconnector_discord",
        "creator",
    )
    fields = (
        "disconnector_discord",
        "disconnected_at",
        "channel_id",
        "channel_name",
        "creator",
    )
