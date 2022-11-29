from django.contrib import admin

from apps.discord.models import DiscordAccount
from apps.overrides.admin import AutofillCreatorModelAdmin


@admin.register(DiscordAccount)
class DiscordAccountAdmin(AutofillCreatorModelAdmin):
    list_display = ("discord_tag", "discord_id", "creator")
    list_filter = ("creator",)
    fields = ("discord_tag", "discord_id", "creator")
