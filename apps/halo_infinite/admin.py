from django.contrib import admin

from apps.halo_infinite.models import (
    HaloInfiniteBuildID,
    HaloInfiniteClearanceToken,
    HaloInfiniteMatch,
    HaloInfinitePlaylist,
    HaloInfiniteSpartanToken,
    HaloInfiniteXSTSToken,
)
from apps.overrides.admin import AutofillCreatorModelAdmin


@admin.register(HaloInfiniteBuildID)
class HaloInfiniteBuildIDAdmin(AutofillCreatorModelAdmin):
    list_display = ("build_id", "build_date", "creator")
    list_filter = ("creator",)
    fields = (
        "build_id",
        "build_date",
        "creator",
    )


@admin.register(HaloInfiniteMatch)
class HaloInfiniteMatchAdmin(AutofillCreatorModelAdmin):
    list_display = ("match_id", "start_time", "end_time", "creator")
    list_filter = (
        "start_time",
        "end_time",
        "creator",
    )
    fields = (
        "match_id",
        "start_time",
        "end_time",
        "data",
        "creator",
    )
    search_fields = ["match_id"]


@admin.register(HaloInfinitePlaylist)
class HaloInfinitePlaylistAdmin(AutofillCreatorModelAdmin):
    list_display = ("name", "description", "active", "creator")
    list_filter = ("active", "ranked", "creator")
    fields = (
        "playlist_id",
        "version_id",
        "name",
        "description",
        "active",
        "ranked",
        "creator",
    )


@admin.register(HaloInfiniteXSTSToken)
class HaloInfiniteXSTSTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "issue_instant", "not_after", "creator")
    list_filter = ("creator",)
    fields = (
        "issue_instant",
        "not_after",
        "token",
        "uhs",
        "creator",
    )


@admin.register(HaloInfiniteSpartanToken)
class HaloInfiniteSpartanTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "created_at", "expires_utc", "creator")
    list_filter = ("creator",)
    fields = (
        "expires_utc",
        "token",
        "token_duration",
        "creator",
    )


@admin.register(HaloInfiniteClearanceToken)
class HaloInfiniteClearanceTokenAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "created_at", "creator")
    list_filter = ("creator",)
    fields = (
        "flight_configuration_id",
        "creator",
    )
