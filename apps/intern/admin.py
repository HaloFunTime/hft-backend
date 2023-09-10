from django.contrib import admin

from apps.intern.models import (
    InternChatter,
    InternChatterForbiddenChannel,
    InternChatterPause,
    InternChatterPauseAcceptanceQuip,
    InternChatterPauseDenialQuip,
    InternChatterPauseReverenceQuip,
    InternHelpfulHint,
    InternNewHereWelcomeQuip,
    InternNewHereYeetQuip,
    InternPassionReportQuip,
    InternPlusRepQuip,
)
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(InternChatter)
class InternChatterAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_message_text", "creator")
    list_filter = ("creator",)
    fields = ("message_text", "creator")


@admin.register(InternChatterForbiddenChannel)
class InternChatterForbiddenChannelAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "discord_channel_id", "discord_channel_name", "creator")
    list_filter = ("creator",)
    fields = ("discord_channel_id", "discord_channel_name", "creator")


@admin.register(InternChatterPause)
class InternChatterPauseAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        "created_at",
        linkify("pauser"),
        "creator",
    )
    list_filter = (
        "pauser",
        "creator",
    )
    fields = ("pauser", "creator")


@admin.register(InternChatterPauseAcceptanceQuip)
class InternChatterPauseAcceptanceQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternChatterPauseDenialQuip)
class InternChatterPauseDenialQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternChatterPauseReverenceQuip)
class InternChatterPauseReverenceQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternHelpfulHint)
class InternHelpfulHintAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_message_text", "creator")
    list_filter = ("creator",)
    fields = ("message_text", "creator")


@admin.register(InternNewHereWelcomeQuip)
class InternNewHereWelcomeQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternNewHereYeetQuip)
class InternNewHereYeetQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternPassionReportQuip)
class InternPassionReportQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternPlusRepQuip)
class InternPlusRepQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "short_quip_text", "creator")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")
