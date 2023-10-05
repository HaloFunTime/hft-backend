from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.season_05.models import (
    Domain,
    DomainChallengeTeamAssignment,
    DomainChallengeTeamReassignment,
    DomainMaster,
)


@admin.register(Domain)
class DomainAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        "playlist",
        "effective_date",
        "created_at",
        "updated_at",
    )
    list_filter = ("effective_date", "creator")
    fields = (
        "name",
        "description",
        "playlist",
        "stat",
        "medal_id",
        "max_score",
        "effective_date",
        "creator",
    )


@admin.register(DomainChallengeTeamAssignment)
class DomainChallengeTeamAssignmentAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("assignee"),
        "team",
        "created_at",
        "updated_at",
    )
    list_filter = ("team", "creator")
    fields = (
        "assignee",
        "team",
        "creator",
    )


@admin.register(DomainChallengeTeamReassignment)
class DomainChallengeTeamReassignmentAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("reassignee"),
        "next_team",
        "reassignment_date",
        "reason",
    )
    list_filter = ("next_team", "reassignment_date", "creator")
    fields = (
        "reassignee",
        "next_team",
        "reassignment_date",
        "reason",
        "creator",
    )


@admin.register(DomainMaster)
class DomainMasterAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["master"]
    list_display = (
        "__str__",
        linkify("master"),
        "mastered_at",
        "domain_count",
        "creator",
    )
    list_filter = ("master", "mastered_at", "domain_count", "creator")
    fields = (
        "master",
        "mastered_at",
        "domain_count",
        "creator",
    )
