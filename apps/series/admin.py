from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin
from apps.series.models import SeriesGametype, SeriesMap, SeriesMode, SeriesRuleset


@admin.register(SeriesMap)
class SeriesMapAdmin(AutofillCreatorModelAdmin):
    list_display = ("name", "hi_asset_id", "hi_version_id", "creator", "id")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "hi_version_id", "creator")


@admin.register(SeriesMode)
class SeriesModeAdmin(AutofillCreatorModelAdmin):
    list_display = ("name", "hi_asset_id", "hi_version_id", "creator", "id")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "hi_version_id", "creator")


@admin.register(SeriesRuleset)
class SeriesRulesetAdmin(AutofillCreatorModelAdmin):
    list_display = ("name", "creator", "id")
    list_filter = ("name",)
    fields = (
        "name",
        "id",
        "featured_mode",
        "allow_bo3_mode_repeats",
        "allow_bo3_map_repeats",
        "allow_bo5_mode_repeats",
        "allow_bo5_map_repeats",
        "allow_bo7_mode_repeats",
        "allow_bo7_map_repeats",
        "creator",
    )


@admin.register(SeriesGametype)
class SeriesGametypeAdmin(AutofillCreatorModelAdmin):
    list_display = ("gametype", "creator", "id")
    list_filter = (
        "map",
        "mode",
    )
    fields = ("ruleset", "mode", "map", "creator")

    def gametype(self, obj):
        return f"{obj.ruleset.name}: {obj.mode.name} on {obj.map.name}"
