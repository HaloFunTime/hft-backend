import logging

from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.trailblazer.models import TrailblazerTuesdayAttendance

logger = logging.getLogger(__name__)


@admin.register(TrailblazerTuesdayAttendance)
class TrailblazerTuesdayAttendanceAdmin(AutofillCreatorModelAdmin):
    autocomplete_fields = ["attendee_discord"]
    list_display = (
        "__str__",
        linkify("attendee_discord"),
        "attendance_date",
        "creator",
    )
    list_filter = ("attendee_discord", "attendance_date", "creator")
    fields = (
        "attendee_discord",
        "attendance_date",
        "creator",
    )
