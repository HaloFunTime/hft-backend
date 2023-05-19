from django.contrib import admin
from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class PathfinderHikeAttendance(Base):
    class Meta:
        db_table = "PathfinderHikeAttendance"
        ordering = [
            "-attendance_date",
        ]
        verbose_name = "Hike Attendance"
        verbose_name_plural = "Hike Attendances"

    attendee_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Attendee Discord",
        related_name="pathfinder_hike_attendees",
    )
    attendance_date = models.DateField(verbose_name="Attendance Date")

    def __str__(self):
        return f"{str(self.attendee_discord)} attended on {self.attendance_date}"


class PathfinderHikeSubmission(Base):
    class Meta:
        db_table = "PathfinderHikeSubmission"
        ordering = [
            "-scheduled_playtest_date",
            "-created_at",
        ]
        verbose_name = "Hike Submission"
        verbose_name_plural = "Hike Submissions"

    waywo_post_title = models.CharField(
        max_length=100, blank=False, verbose_name="WAYWO Post Title"
    )
    waywo_post_id = models.CharField(
        max_length=20, blank=False, verbose_name="WAYWO Post ID"
    )
    max_player_count = models.CharField(
        max_length=32, verbose_name="Max Player Count", null=True
    )
    map_submitter_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Map Submitter Discord",
        related_name="pathfinder_hike_submitters",
    )
    scheduled_playtest_date = models.DateField(
        verbose_name="Scheduled Playtest Date", null=True, blank=True
    )
    map = models.CharField(max_length=32, verbose_name="Map")
    mode_1 = models.CharField(max_length=32, verbose_name="Mode 1")
    mode_2 = models.CharField(max_length=32, verbose_name="Mode 2")
    mode_1_played = models.BooleanField(
        default=False, verbose_name="Was Mode 1 played?"
    )
    mode_2_played = models.BooleanField(
        default=False, verbose_name="Was Mode 2 played?"
    )
    submitter_present_for_playtest = models.BooleanField(
        default=False, verbose_name="Was the map submitter present for the playtest?"
    )

    @admin.display(boolean=True)
    def playtested(self):
        return self.mode_1_played or self.mode_2_played

    @admin.display(boolean=True)
    def fully_playtested(self):
        return self.mode_1_played and self.mode_2_played

    def __str__(self):
        schedule_string = (
            str(self.scheduled_playtest_date)
            if self.scheduled_playtest_date is not None
            else "Unscheduled"
        )
        return f"{schedule_string}: {self.map}"


class PathfinderWAYWOPost(Base):
    class Meta:
        db_table = "PathfinderWAYWOPost"
        ordering = [
            "-created_at",
        ]
        verbose_name = "WAYWO Post"
        verbose_name_plural = "WAYWO Posts"

    post_title = models.CharField(
        max_length=100, blank=False, verbose_name="Post Title"
    )
    post_id = models.CharField(max_length=20, blank=False, verbose_name="Post ID")
    poster_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Poster Discord",
        related_name="pathfinder_waywo_posters",
    )

    def __str__(self):
        return self.post_title
