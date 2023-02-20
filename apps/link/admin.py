from django.contrib import admin

from apps.link.models import DiscordXboxLiveLink
from apps.overrides.admin import AutofillCreatorModelAdmin


@admin.register(DiscordXboxLiveLink)
class DiscordXboxLiveLinkAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "discord_account", "xbox_live_account", "verified", "creator")
    list_filter = ("creator",)
    fields = ("discord_account", "xbox_live_account", "verified", "creator")
