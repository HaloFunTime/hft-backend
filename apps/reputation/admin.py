from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.reputation.models import PlusRep


@admin.register(PlusRep)
class PlusRepAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["giver", "receiver"]
    list_display = (
        "id",
        "created_at",
        linkify("giver"),
        linkify("receiver"),
        "message",
        "creator",
    )
    list_filter = (
        "giver",
        "receiver",
        "creator",
    )
    fields = ("giver", "receiver", "message", "creator")
