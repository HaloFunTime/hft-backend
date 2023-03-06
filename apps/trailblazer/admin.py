import logging

from django.contrib import admin

from apps.overrides.admin import AutofillCreatorModelAdmin, linkify
from apps.trailblazer.models import (
    TrailblazerTuesdayAttendance,
    TrailblazerTuesdayReferral,
    TrailblazerVODReview,
)

logger = logging.getLogger(__name__)


@admin.register(TrailblazerTuesdayAttendance)
class TrailblazerTuesdayAttendanceAdmin(AutofillCreatorModelAdmin):
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


@admin.register(TrailblazerTuesdayReferral)
class TrailblazerTuesdayReferralAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("referrer_discord"),
        linkify("invitee_discord"),
        "referral_date",
        "creator",
    )
    list_filter = ("referrer_discord", "invitee_discord", "referral_date", "creator")
    fields = (
        "referrer_discord",
        "invitee_discord",
        "referral_date",
        "creator",
    )


@admin.register(TrailblazerVODReview)
class TrailblazerVODReviewAdmin(AutofillCreatorModelAdmin):
    list_display = (
        "__str__",
        linkify("submitter_discord"),
        "submission_date",
        "submission_link",
        "creator",
    )
    list_filter = ("submitter_discord", "submission_date", "creator")
    fields = (
        "submitter_discord",
        "submission_date",
        "submission_link",
        "submission_notes",
        "creator",
    )
