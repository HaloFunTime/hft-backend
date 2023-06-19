from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.showcase.models import ShowcaseFile, ShowcaseFileSnapshot


@admin.register(ShowcaseFile)
class ShowcaseFileAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["showcase_owner"]
    list_display = (
        "__str__",
        linkify("showcase_owner"),
        "file_type",
        "file_id",
        "created_at",
    )
    list_filter = ("showcase_owner", "file_type", "creator")
    fields = (
        "showcase_owner",
        "file_type",
        "file_id",
        "position",
        "creator",
    )


@admin.register(ShowcaseFileSnapshot)
class ShowcaseFileSnapshotAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("file"),
        "version_id",
        "snapshot_date",
        "creator",
    )
    list_filter = ("file", "snapshot_date", "creator")
    fields = (
        "file",
        "version_id",
        "name",
        "description",
        "snapshot_date",
        "plays_recent",
        "plays_all_time",
        "favorites",
        "number_of_ratings",
        "average_rating",
        "creator",
    )
