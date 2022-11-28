from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin
from apps.xbox_live.models import XboxLiveAccount


@admin.register(XboxLiveAccount)
class XboxLiveAccountAdmin(AutofillCreatorModelAdmin):
    list_display = ("gamertag", "creator")
    list_filter = ("creator",)
    fields = ("gamertag", "creator")
