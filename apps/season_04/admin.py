from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.season_04.models import StampChampEarner


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
