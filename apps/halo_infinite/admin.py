from django.contrib import admin

from apps.halo_infinite.models import (
    HaloInfiniteBuildID,
    HaloInfiniteClearanceToken,
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
