from django.contrib import admin

from apps.series.models import SeriesGametype, SeriesMap, SeriesMode, SeriesRuleset


@admin.register(SeriesMap)
class SeriesMapAdmin(admin.ModelAdmin):
    list_display = ("name", "hi_asset_id", "hi_version_id", "creator", "id")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "hi_version_id", "creator")

    def add_view(self, request, form_url="", extra_context=None):
        creator = request.GET.get("creator", None)
        if creator is None:
            g = request.GET.copy()
            g.update(
                {
                    "creator": request.user,
                }
            )
            request.GET = g
        return super().add_view(request, form_url, extra_context)


@admin.register(SeriesMode)
class SeriesModeAdmin(admin.ModelAdmin):
    list_display = ("name", "hi_asset_id", "hi_version_id", "creator", "id")
    list_filter = ("name",)
    fields = ("name", "hi_asset_id", "hi_version_id", "creator")

    def add_view(self, request, form_url="", extra_context=None):
        creator = request.GET.get("creator", None)
        if creator is None:
            g = request.GET.copy()
            g.update(
                {
                    "creator": request.user,
                }
            )
            request.GET = g
        return super().add_view(request, form_url, extra_context)


@admin.register(SeriesRuleset)
class SeriesRulesetAdmin(admin.ModelAdmin):
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

    def add_view(self, request, form_url="", extra_context=None):
        creator = request.GET.get("creator", None)
        if creator is None:
            g = request.GET.copy()
            g.update(
                {
                    "creator": request.user,
                }
            )
            request.GET = g
        return super().add_view(request, form_url, extra_context)


@admin.register(SeriesGametype)
class SeriesGametypeAdmin(admin.ModelAdmin):
    list_display = ("gametype", "creator", "id")
    list_filter = (
        "map",
        "mode",
    )
    fields = ("ruleset", "mode", "map", "creator")

    def add_view(self, request, form_url="", extra_context=None):
        creator = request.GET.get("creator", None)
        if creator is None:
            g = request.GET.copy()
            g.update(
                {
                    "creator": request.user,
                }
            )
            request.GET = g
        return super().add_view(request, form_url, extra_context)

    def gametype(self, obj):
        return f"{obj.ruleset.name}: {obj.mode.name} on {obj.map.name}"
