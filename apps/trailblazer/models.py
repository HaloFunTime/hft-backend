from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class TrailblazerExcellentVODReview(Base):
    class Meta:
        db_table = "TrailblazerExcellentVODReview"
        ordering = [
            "-review_date",
        ]
        verbose_name = "Excellent VOD Review"
        verbose_name_plural = "Excellent VOD Reviews"

    reviewer_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Reviewer Discord",
        related_name="trailblazer_excellent_vod_reviewers",
    )
    review_date = models.DateField(verbose_name="Review Date")
    review_message_link = models.CharField(
        max_length=512, blank=True, verbose_name="Review Message Link"
    )

    def __str__(self):
        return f"{str(self.reviewer_discord)} reviewed on {self.review_date}"


class TrailblazerTuesdayAttendance(Base):
    class Meta:
        db_table = "TrailblazerTuesdayAttendance"
        ordering = [
            "-attendance_date",
        ]
        verbose_name = "Tuesday Attendance"
        verbose_name_plural = "Tuesday Attendances"

    attendee_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Attendee Discord",
        related_name="trailblazer_tuesday_attendees",
    )
    attendance_date = models.DateField(verbose_name="Attendance Date")

    def __str__(self):
        return f"{str(self.attendee_discord)} attended on {self.attendance_date}"


class TrailblazerTuesdayReferral(Base):
    class Meta:
        db_table = "TrailblazerTuesdayReferral"
        ordering = [
            "-referral_date",
        ]
        verbose_name = "Tuesday Referral"
        verbose_name_plural = "Tuesday Referrals"

    referrer_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Referrer Discord",
        related_name="trailblazer_tuesday_referrers",
    )
    invitee_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Invitee Discord",
        related_name="trailblazer_tuesday_invitees",
    )
    referral_date = models.DateField(verbose_name="Referral Date")

    def __str__(self):
        return f"{str(self.referrer_discord)} invited {str(self.invitee_discord)}"


class TrailblazerVODSubmission(Base):
    class Meta:
        db_table = "TrailblazerVODSubmission"
        ordering = [
            "-submission_date",
        ]
        verbose_name = "VOD Submission"
        verbose_name_plural = "VOD Submissions"

    submitter_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Submitter Discord",
        related_name="trailblazer_vod_submitters",
    )
    submission_date = models.DateField(verbose_name="Submission Date")
    submission_link = models.CharField(
        max_length=512, blank=True, verbose_name="Submission Link"
    )
    submission_notes = models.TextField(blank=True, verbose_name="Submission Notes")

    def __str__(self):
        return f"{str(self.submitter_discord)} submitted on {self.submission_date}"
