import logging

from django.contrib import admin

from apps.link.models import DiscordXboxLiveLink
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify

logger = logging.getLogger(__name__)


@admin.register(DiscordXboxLiveLink)
class DiscordXboxLiveLinkAdmin(AutofillCreatorModelAdmin):
    # Override `save_model` to log whoever verified someone's gamertag
    def save_model(self, request, obj, form, change):
        if change:
            old_obj = DiscordXboxLiveLink.objects.get(id=obj.id)
            if obj.verified and not old_obj.verified:
                logger.debug(f"{obj} verified by {request.user}")
                obj.verifier = request.user
            elif old_obj.verified and not obj.verified:
                logger.debug(f"{obj} unverified by {request.user}")
                obj.verifier = None
        super().save_model(request, obj, form, change)

    autocomplete_fields = ["discord_account", "xbox_live_account"]
    list_display = (
        "__str__",
        linkify("discord_account"),
        linkify("xbox_live_account"),
        "verified",
        "verifier",
    )
    list_filter = (
        "verified",
        "verifier",
        "creator",
    )
    fields = ("discord_account", "xbox_live_account", "verified", "verifier", "creator")
