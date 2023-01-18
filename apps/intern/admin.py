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
    InternPlusRepQuip,
)
from apps.overrides.admin import AutofillCreatorModelAdmin


@admin.register(InternChatter)
class InternChatterAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_message_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("message_text", "creator")


@admin.register(InternChatterForbiddenChannel)
class InternChatterForbiddenChannelAdmin(AutofillCreatorModelAdmin):
    list_display = ("discord_channel_id", "discord_channel_name", "creator", "id")
    list_filter = ("creator",)
    fields = ("discord_channel_id", "discord_channel_name", "creator")


@admin.register(InternChatterPause)
class InternChatterPauseAdmin(AutofillCreatorModelAdmin):
    list_display = ("created_at", "discord_user_id", "discord_user_tag", "creator")
    list_filter = ("creator",)
    fields = ("discord_user_id", "discord_user_tag", "creator")


@admin.register(InternChatterPauseAcceptanceQuip)
class InternChatterPauseAcceptanceQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternChatterPauseDenialQuip)
class InternChatterPauseDenialQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternChatterPauseReverenceQuip)
class InternChatterPauseReverenceQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternHelpfulHint)
class InternHelpfulHintAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_message_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("message_text", "creator")


@admin.register(InternNewHereWelcomeQuip)
class InternNewHereWelcomeQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternNewHereYeetQuip)
class InternNewHereYeetQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")


@admin.register(InternPlusRepQuip)
class InternPlusRepQuipAdmin(AutofillCreatorModelAdmin):
    list_display = ("short_quip_text", "creator", "id")
    list_filter = ("creator",)
    fields = ("quip_text", "creator")
