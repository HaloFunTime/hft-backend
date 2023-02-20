from django.contrib import admin

from apps.link.models import DiscordXboxLiveLink
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(DiscordXboxLiveLink)
class DiscordXboxLiveLinkAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("discord_account"),
        linkify("xbox_live_account"),
        "verified",
        "creator",
    )
    list_filter = ("creator",)
    fields = ("discord_account", "xbox_live_account", "verified", "creator")
