from django.contrib import admin

from apps.intern.models import (
    InternChatter,
    InternChatterForbiddenChannel,
    InternChatterPause,
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
