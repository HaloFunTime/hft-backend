from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class PathfinderBeanCount(Base):
    class Meta:
        db_table = "PathfinderBeanCount"
        ordering = [
            "-bean_count",
        ]
        verbose_name = "Bean Count"
        verbose_name_plural = "Bean Counts"

    bean_owner_discord = models.OneToOneField(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Bean Owner Discord",
        related_name="pathfinder_bean_owners",
    )
    bean_count = models.IntegerField(verbose_name="Bean Count", default=0)

    def __str__(self):
        return f"{str(self.bean_owner_discord)}: {self.bean_count} bean{'s' if self.bean_count != 1 else ''}"


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
        null=True,
    )
    scheduled_playtest_date = models.DateField(
        verbose_name="Scheduled Playtest Date", null=True, blank=True
    )
    map = models.CharField(max_length=32, verbose_name="Map")
    mode = models.CharField(max_length=32, verbose_name="Mode", default="Slayer")
    playtest_game_id = models.UUIDField(
        verbose_name="Playtest Game ID", null=True, blank=True
    )

    @property
    def playtest_game_link(self):
        return (
            ""
            if self.playtest_game_id is None
            else format_html(
                f"<a href=https://leafapp.co/game/{self.playtest_game_id}>View on LeafApp</a>"
            )
        )

    @admin.display(boolean=True)
    def playtested(self):
        return self.playtest_game_id is not None

    def __str__(self):
        schedule_string = (
            str(self.scheduled_playtest_date)
            if self.scheduled_playtest_date is not None
            else "Unscheduled"
        )
        return f"{schedule_string}: {self.waywo_post_title}"


class PathfinderHikeGameParticipation(Base):
    class Meta:
        db_table = "PathfinderHikeGameParticipation"
        ordering = ["-created_at"]
        verbose_name = "Pathfinder Hike Game Participation"
        verbose_name_plural = "Pathfinder Hike Game Participations"

    hike_submission = models.ForeignKey(
        PathfinderHikeSubmission, on_delete=models.CASCADE
    )
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class PathfinderHikeVoiceParticipation(Base):
    class Meta:
        db_table = "PathfinderHikeVoiceParticipation"
        ordering = ["-created_at"]
        verbose_name = "Pathfinder Hike Voice Participation"
        verbose_name_plural = "Pathfinder Hike Voice Participations"

    hike_submission = models.ForeignKey(
        PathfinderHikeSubmission, on_delete=models.CASCADE
    )
    discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="pathfinder_hike_voice_participants",
    )


class PathfinderWAYWOComment(Base):
    class Meta:
        db_table = "PathfinderWAYWOComment"
        ordering = [
            "-created_at",
        ]
        verbose_name = "WAYWO Comment"
        verbose_name_plural = "WAYWO Comments"

    post_id = models.CharField(max_length=20, blank=False, verbose_name="Post ID")
    comment_id = models.CharField(max_length=20, blank=False, verbose_name="Comment ID")
    commenter_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Commenter Discord",
        related_name="pathfinder_waywo_commenters",
    )
    comment_length = models.IntegerField(verbose_name="Comment Length")

    def __str__(self):
        return self.comment_id


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
