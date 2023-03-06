import logging

from django.contrib import admin
from django.db.models import Q

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.pathfinder.models import PathfinderHikeSubmission

logger = logging.getLogger(__name__)


class IsPlaytestedFilter(admin.SimpleListFilter):
    title = " Playtested"
    parameter_name = "is_playtested"

    def lookups(self, request, model_admin):
        return (
            ("Yes", "Yes"),
            ("No", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.filter(Q(mode_1_played=True) | Q(mode_2_played=True))
        elif value == "No":
            return queryset.filter(Q(mode_1_played=False) & Q(mode_2_played=False))
        return queryset


class IsFullyPlaytestedFilter(admin.SimpleListFilter):
    title = "Fully Playtested"
    parameter_name = "is_fully_playtested"

    def lookups(self, request, model_admin):
        return (
            ("Yes", "Yes"),
            ("No", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.filter(Q(mode_1_played=True) & Q(mode_2_played=True))
        elif value == "No":
            return queryset.filter(Q(mode_1_played=False) | Q(mode_2_played=False))
        return queryset


@admin.register(PathfinderHikeSubmission)
class PathfinderHikeSubmissionAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("map_submitter_discord"),
        "mode_1",
        "mode_2",
        "playtested",
        "fully_playtested",
    )
    list_filter = (
        "scheduled_playtest_date",
        IsPlaytestedFilter,
        IsFullyPlaytestedFilter,
        "map_submitter_discord",
    )
    fields = (
        "waywo_post_title",
        "waywo_post_id",
        "map_submitter_discord",
        "scheduled_playtest_date",
        "map",
        "mode_1",
        "mode_2",
        "mode_1_played",
        "mode_2_played",
        "submitter_present_for_playtest",
        "creator",
    )
