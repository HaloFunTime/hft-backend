import logging

from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.pathfinder.models import (
    PathfinderBeanCount,
    PathfinderHikeSubmission,
    PathfinderWAYWOComment,
    PathfinderWAYWOPost,
)

logger = logging.getLogger(__name__)


class IsPlaytestedFilter(admin.SimpleListFilter):
    title = "Playtested"
    parameter_name = "is_playtested"

    def lookups(self, request, model_admin):
        return (
            ("Yes", "Yes"),
            ("No", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "Yes":
            return queryset.filter(playtest_game_id__isnull=False)
        elif value == "No":
            return queryset.filter(playtest_game_id__isnull=True)
        return queryset


@admin.register(PathfinderBeanCount)
class PathfinderBeanCountAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["bean_owner_discord"]
    list_display = (
        "__str__",
        linkify("bean_owner_discord"),
        "bean_count",
    )
    list_filter = (
        "bean_count",
        "bean_owner_discord",
    )
    fields = (
        "bean_owner_discord",
        "bean_count",
        "creator",
    )


@admin.register(PathfinderHikeSubmission)
class PathfinderHikeSubmissionAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["map_submitter_discord"]
    list_display = (
        "__str__",
        linkify("map_submitter_discord"),
        "max_player_count",
        "mode",
        "playtest_game_link",
    )
    list_filter = (
        "scheduled_playtest_date",
        IsPlaytestedFilter,
        "map_submitter_discord",
    )
    fields = (
        "waywo_post_title",
        "waywo_post_id",
        "map_submitter_discord",
        "scheduled_playtest_date",
        "max_player_count",
        "map",
        "mode",
        "playtest_game_id",
        "creator",
    )


@admin.register(PathfinderWAYWOPost)
class PathfinderWAYWOPostAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["poster_discord"]
    list_display = (
        "__str__",
        linkify("poster_discord"),
        "post_title",
        "post_id",
        "creator",
    )
    list_filter = (
        "poster_discord",
        "creator",
    )
    fields = (
        "poster_discord",
        "post_id",
        "post_title",
        "creator",
    )


@admin.register(PathfinderWAYWOComment)
class PathfinderWAYWOCommentAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["commenter_discord"]
    list_display = (
        "__str__",
        linkify("commenter_discord"),
        "post_id",
        "comment_id",
        "comment_length",
        "creator",
    )
    list_filter = (
        "commenter_discord",
        "creator",
    )
    fields = (
        "commenter_discord",
        "post_id",
        "comment_id",
        "comment_length",
        "creator",
    )
