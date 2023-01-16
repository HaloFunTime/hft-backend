from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin
from apps.reputation.models import PlusRep


@admin.register(PlusRep)
class PlusRepAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "created_at",
        "updated_at",
        "giver",
        "receiver",
        "message",
        "creator",
    )
    list_filter = ("creator",)
    fields = ("giver", "receiver", "message", "creator")
