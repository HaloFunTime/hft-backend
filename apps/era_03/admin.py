from django.contrib import admin

from apps.era_03.models import (
    BoatAssignment,
    BoatCaptain,
    BoatDeckhand,
    BoatRank,
    BoatSecret,
    BoatSecretUnlock,
    WeeklyBoatAssignments,
)
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(BoatAssignment)
class BoatAssignmentAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "classification",
        "description",
    )
    list_filter = ("classification", "stat", "creator")
    fields = (
        "classification",
        "description",
        "stat",
        "score",
        "require_outcome",
        "require_level_id",
        "require_map_asset_id",
        "require_mode_asset_id",
        "require_playlist_asset_id",
        "creator",
    )


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


@admin.register(BoatSecret)
class BoatSecretAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "hint",
        "creator",
    )
    list_filter = ("creator",)
    fields = (
        "medal_id",
        "title",
        "hint",
        "creator",
    )


@admin.register(BoatSecretUnlock)
class BoatSecretUnlockAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "external_match_link",
        "created_at",
    )
    list_filter = ("deckhand", "secret", "creator")
    fields = (
        "deckhand",
        "secret",
        "match",
        "creator",
    )


@admin.register(WeeklyBoatAssignments)
class WeeklyBoatAssignmentsAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "deckhand",
        "week_start",
        "creator",
    )
    list_filter = ("deckhand", "week_start", "creator")
    fields = (
        "deckhand",
        "week_start",
        "assignment_1",
        "assignment_1_completion_match_id",
        "assignment_2",
        "assignment_2_completion_match_id",
        "assignment_3",
        "assignment_3_completion_match_id",
        "next_rank",
        "creator",
    )
