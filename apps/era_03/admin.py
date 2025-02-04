from django.contrib import admin

from apps.era_03.models import BoatCaptain, BoatDeckhand, BoatRank
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(BoatCaptain)
class BoatCaptainAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["earner"]
    list_display = (
        "__str__",
        linkify("earner"),
        "earned_at",
        "rank_tier",
        "creator",
    )
    list_filter = ("earner", "earned_at", "rank_tier", "creator")
    fields = (
        "earner",
        "earned_at",
        "rank_tier",
        "creator",
    )


@admin.register(BoatDeckhand)
class BoatDeckhandAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("deckhand"),
        linkify("rank"),
        "created_at",
        "updated_at",
    )
    list_filter = ("rank", "creator")
    fields = (
        "deckhand",
        "rank",
        "most_recent_match_id",
        "creator",
    )


@admin.register(BoatRank)
class BoatRankAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "updated_at",
    )
    list_filter = ("tier", "track", "creator")
    fields = (
        "rank",
        "tier",
        "track",
        "description",
        "creator",
    )
