from django.contrib import admin

from apps.discord.models import DiscordAccount
from apps.overrides.admin import AutofillCreatorModelAdmin


@admin.register(DiscordAccount)
class DiscordAccountAdmin(AutofillCreatorModelAdmin):
    list_display = ("discord_id", "discord_tag", "creator")
    list_filter = ("creator",)
    fields = ("discord_tag", "discord_id", "creator")
