from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.season_06.models import BingoBuff, BingoChallengeParticipant


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
        "creator",
    )
