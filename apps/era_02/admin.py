from django.contrib import admin

from apps.era_02.models import MVT, TeamUpChallengeCompletion
from apps.overrides.admin import AutofillCreatorModelAdmin, linkify


@admin.register(MVT)
class MVTAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["earner"]
    list_display = (
        "__str__",
        linkify("earner"),
        "earned_at",
        "mvt_points",
        "creator",
    )
    list_filter = ("earner", "earned_at", "mvt_points", "creator")
    fields = (
        "earner",
        "earned_at",
        "bingo_count",
        "creator",
    )


@admin.register(TeamUpChallengeCompletion)
class TeamUpChallengeCompletionAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["xbox_account", "match"]
    list_display = (
        "created_at",
        "challenge",
        linkify("xbox_account"),
        linkify("match"),
        "external_match_link",
    )
    list_filter = (
        "challenge",
        "xbox_account",
        "creator",
    )
    fields = (
        "challenge",
        "xbox_account",
        "match",
        "creator",
    )
