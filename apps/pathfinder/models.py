from django.contrib import admin
from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


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
    map_submitter_discord = models.ForeignKey(
        DiscordAccount, on_delete=models.RESTRICT, verbose_name="Map Submitter Discord"
    )
    scheduled_playtest_date = models.DateField(verbose_name="Scheduled Playtest Date")
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
        return f"{str(self.scheduled_playtest_date)}: {self.map}"
