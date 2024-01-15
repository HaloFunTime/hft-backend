from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.season_06.models import (
    BingoBuff,
    BingoChallenge,
    BingoChallengeCompletion,
    BingoChallengeParticipant,
)


@admin.register(BingoBuff)
class BingoBuffAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["earner"]
    list_display = (
        "__str__",
        linkify("earner"),
        "earned_at",
        "bingo_count",
        "challenge_count",
        "creator",
    )
    list_filter = ("earner", "earned_at", "bingo_count", "challenge_count", "creator")
    fields = (
        "earner",
        "earned_at",
        "bingo_count",
        "challenge_count",
        "creator",
    )


@admin.register(BingoChallengeParticipant)
class BingoChallengeParticipantAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("participant"),
        "board_order",
        "created_at",
        "updated_at",
    )
    list_filter = ("board_order", "creator")
    fields = (
        "participant",
        "board_order",
        "most_recent_match_id",
        "creator",
    )


@admin.register(BingoChallenge)
class BingoChallengeAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "description",
        "updated_at",
    )
    list_filter = ("require_match_type", "stat", "creator")
    fields = (
        "id",
        "name",
        "description",
        "require_match_type",
        "require_outcome",
        "require_level_id",
        "require_map_asset_id",
        "require_mode_asset_id",
        "require_playlist_asset_id",
        "require_present_at_beginning",
        "require_present_at_completion",
        "stat",
        "medal_id",
        "score",
        "creator",
    )


@admin.register(BingoChallengeCompletion)
class BingoChallengeCompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "created_at",
        linkify("challenge"),
        linkify("participant"),
        linkify("match"),
    )
    list_filter = ("challenge", "participant", "creator")
    fields = (
        "challenge",
        "participant",
        "match",
        "creator",
    )
