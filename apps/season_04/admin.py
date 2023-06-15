from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.season_04.models import (
    StampChallenge16Completion,
    StampChallenge17Completion,
    StampChallenge18Completion,
    StampChallenge19Completion,
    StampChallenge20Completion,
    StampChallengeBTBMatch,
    StampChampEarner,
)


@admin.register(StampChallengeBTBMatch)
class StampChallengeBTBMatchAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "match_id",
        "challenge",
        "match_link",
        "created_at",
    )
    list_filter = ("challenge", "creator")
    fields = (
        "challenge",
        "match_id",
        "creator",
    )


@admin.register(StampChallenge16Completion)
class StampChallenge16CompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        linkify("match"),
        "xuid",
    )
    list_filter = ("match", "xuid", "creator")
    fields = (
        "match",
        "xuid",
        "creator",
    )


@admin.register(StampChallenge17Completion)
class StampChallenge17CompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        linkify("match"),
        "xuid",
    )
    list_filter = ("match", "xuid", "creator")
    fields = (
        "match",
        "xuid",
        "creator",
    )


@admin.register(StampChallenge18Completion)
class StampChallenge18CompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        linkify("match"),
        "xuid",
    )
    list_filter = ("match", "xuid", "creator")
    fields = (
        "match",
        "xuid",
        "creator",
    )


@admin.register(StampChallenge19Completion)
class StampChallenge19CompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        linkify("match"),
        "xuid",
    )
    list_filter = ("match", "xuid", "creator")
    fields = (
        "match",
        "xuid",
        "creator",
    )


@admin.register(StampChallenge20Completion)
class StampChallenge20CompletionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "id",
        linkify("match"),
        "xuid",
    )
    list_filter = ("match", "xuid", "creator")
    fields = (
        "match",
        "xuid",
        "creator",
    )


@admin.register(StampChampEarner)
class StampChampEarnerAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["earner"]
    list_display = (
        "__str__",
        linkify("earner"),
        "earned_at",
        "creator",
    )
    list_filter = ("earner", "earned_at", "creator")
    fields = (
        "earner",
        "earned_at",
        "creator",
    )
