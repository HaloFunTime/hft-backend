from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.series.models import SeriesGametype, SeriesMap, SeriesMode, SeriesRuleset


@admin.register(SeriesMap)
class SeriesMapAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "name", "hi_asset_id", "creator")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "creator")


@admin.register(SeriesMode)
class SeriesModeAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "name", "hi_asset_id", "creator")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "creator")


@admin.register(SeriesRuleset)
class SeriesRulesetAdmin(AutofillCreatorModelAdmin):
    list_display = ("id", "name", "creator")
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
    list_display = (
        "id",
        linkify("ruleset"),
        linkify("mode"),
        linkify("map"),
        "creator",
    )
    list_filter = (
        "ruleset",
        "mode",
        "map",
    )
    fields = ("ruleset", "mode", "map", "creator")

    def gametype(self, obj):
        return f"{obj.ruleset.name}: {obj.mode.name} on {obj.map.name}"
