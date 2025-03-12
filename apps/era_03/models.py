from calendar import TUESDAY
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.html import format_html

from apps.discord.models import DiscordAccount
from apps.halo_infinite.constants import STATS
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.overrides.models import Base


def get_stat_choices():
    choices = []
    for key in STATS:
        if key != "CoreStats_Medals":
            choices.append(
                (key, f"{key.split('_')[0].rstrip('Stats')}: {STATS.get(key)[1]}")
            )
    return choices


def validate_tuesday_only(value: date):
    if value.weekday() != TUESDAY:
        raise ValidationError("The date must be a Tuesday.")


class BoatRank(Base):
    class Meta:
        db_table = "BoatRank"
        ordering = ["tier", "track"]
        verbose_name = "Rank"
        verbose_name_plural = "Ranks"

    class Tracks(models.TextChoices):
        NA = "N/A", "N/A"
        COMMAND = "Command", "Command"
        MACHINERY = "Machinery", "Machinery"
        HOSPITALITY = "Hospitality", "Hospitality"
        CULINARY = "Culinary", "Culinary"

    rank = models.CharField(max_length=255, verbose_name="Rank")
    tier = models.IntegerField(verbose_name="Tier", validators=[MinValueValidator(1)])
    track = models.CharField(
        max_length=255,
        verbose_name="Track",
        choices=Tracks.choices,
        default=Tracks.NA,
    )
    description = models.TextField(verbose_name="Description", null=True, blank=True)

    def __str__(self):
        return f"{self.rank}: Tier {self.tier} {'' if self.track == self.Tracks.NA else f'({self.track} Track)'}"


class BoatCaptain(Base):
    class Meta:
        db_table = "BoatCaptain"
        ordering = ["-created_at"]
        verbose_name = "Boat Captain"
        verbose_name_plural = "Boat Captains"

    earner = models.OneToOneField(
        DiscordAccount, on_delete=models.RESTRICT, related_name="boat_captain"
    )
    earned_at = models.DateTimeField()
    rank_tier = models.IntegerField(
        verbose_name="Rank Tier", validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f"{self.earner} ({self.earned_at})"


class BoatDeckhand(Base):
    class Meta:
        db_table = "BoatDeckhand"
        ordering = ["-created_at"]
        verbose_name = "Deckhand"
        verbose_name_plural = "Deckhands"

    deckhand = models.OneToOneField(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="deckhands",
        verbose_name="Deckhand",
    )
    rank = models.ForeignKey(
        BoatRank,
        on_delete=models.RESTRICT,
        related_name="deckhands",
        verbose_name="Rank",
    )
    most_recent_match_id = models.UUIDField(
        null=True, blank=True, verbose_name="Most Recent Match ID"
    )

    def __str__(self):
        return f"{self.deckhand}"


class BoatAssignment(Base):
    class Meta:
        db_table = "BoatAssignment"
        ordering = ["-created_at"]
        verbose_name = "Boat Assignment"
        verbose_name_plural = "Boat Assignments"

    class Classification(models.TextChoices):
        EASY = "Easy"
        MEDIUM = "Medium"
        HARD = "Hard"
        COMMAND = "Command"
        MACHINERY = "Machinery"
        HOSPITALITY = "Hospitality"
        CULINARY = "Culinary"

    class Outcome(models.IntegerChoices):
        WIN = 2
        LOSS = 3
        TIE = 1
        LEFT = 4

    classification = models.CharField(
        max_length=255, choices=Classification.choices, verbose_name="Classification"
    )
    description = models.TextField(
        max_length=256, verbose_name="Description", null=True, blank=True
    )
    stat = models.CharField(
        max_length=128, choices=get_stat_choices, verbose_name="Stat"
    )
    score = models.CharField(max_length=128, verbose_name="Score")
    require_outcome = models.IntegerField(
        blank=True,
        null=True,
        choices=Outcome.choices,
        verbose_name="Outcome",
    )
    require_level_id = models.UUIDField(
        blank=True, null=True, verbose_name="Level Canvas ID"
    )
    require_map_asset_id = models.UUIDField(
        blank=True, null=True, verbose_name="Map File ID"
    )
    require_mode_asset_id = models.UUIDField(
        blank=True, null=True, verbose_name="Mode File ID"
    )
    require_playlist_asset_id = models.UUIDField(
        blank=True, null=True, verbose_name="Playlist ID"
    )

    def __str__(self):
        return f"{self.classification} - {self.description}"


class BoatSecret(Base):
    class Meta:
        db_table = "BoatSecret"
        ordering = ["-created_at"]
        verbose_name = "Boat Secret"
        verbose_name_plural = "Boat Secrets"

    medal_id = models.DecimalField(
        decimal_places=0, max_digits=15, verbose_name="Medal ID"
    )
    title = models.TextField(max_length=64, verbose_name="Title")
    hint = models.TextField(max_length=256, verbose_name="Hint")

    def __str__(self):
        return self.title


class BoatSecretUnlock(Base):
    class Meta:
        db_table = "BoatSecretUnlock"
        ordering = ["-created_at"]
        verbose_name = "Boat Secret Unlock"
        verbose_name_plural = "Boat Secret Unlocks"

    secret = models.ForeignKey(
        BoatSecret,
        on_delete=models.RESTRICT,
        related_name="unlocks",
        verbose_name="Secret",
    )
    deckhand = models.ForeignKey(
        BoatDeckhand,
        on_delete=models.RESTRICT,
        related_name="secrets_unlocked",
        verbose_name="Deckhand",
    )
    match = models.ForeignKey(
        HaloInfiniteMatch,
        on_delete=models.CASCADE,
        related_name="+",
    )

    @property
    def external_match_link(self):
        return (
            ""
            if self.match_id is None
            else format_html(
                f"<a href=https://halotracker.com/halo-infinite/match/{self.match_id}>View on HaloTracker</a>"
            )
        )

    def __str__(self):
        return f"{self.deckhand} unlocked {self.secret}"


class WeeklyBoatAssignments(Base):
    class Meta:
        db_table = "WeeklyBoatAssignments"
        ordering = ["-created_at"]
        verbose_name = "Weekly Boat Assignments"
        verbose_name_plural = "Weekly Boat Assignments"

    deckhand = models.ForeignKey(
        BoatDeckhand,
        on_delete=models.RESTRICT,
        related_name="weekly_assignments",
        verbose_name="Deckhand",
    )
    week_start = models.DateField(
        verbose_name="Week Start",
        validators=[MinValueValidator(date(2025, 2, 4)), validate_tuesday_only],
    )
    assignment_1 = models.ForeignKey(
        BoatAssignment,
        on_delete=models.RESTRICT,
        related_name="assignment_1",
        verbose_name="Assignment 1",
    )
    assignment_1_completion_match_id = models.UUIDField(
        blank=True, null=True, verbose_name="Assignment 1 Completion Match ID"
    )
    assignment_2 = models.ForeignKey(
        BoatAssignment,
        on_delete=models.RESTRICT,
        related_name="assignment_2",
        verbose_name="Assignment 2",
        null=True,
        blank=True,
    )
    assignment_2_completion_match_id = models.UUIDField(
        blank=True, null=True, verbose_name="Assignment 2 Completion Match ID"
    )
    assignment_3 = models.ForeignKey(
        BoatAssignment,
        on_delete=models.RESTRICT,
        related_name="assignment_3",
        verbose_name="Assignment 3",
        null=True,
        blank=True,
    )
    assignment_3_completion_match_id = models.UUIDField(
        blank=True, null=True, verbose_name="Assignment 3 Completion Match ID"
    )
    next_rank = models.ForeignKey(
        BoatRank,
        on_delete=models.RESTRICT,
        related_name="next_rank",
        verbose_name="Next Rank",
    )

    def __str__(self):
        return f"{self.deckhand} - {self.week_start.strftime('%Y-%m-%d')} Weekly Assignments"

    @property
    def completed_all_assignments(self) -> bool:
        return (
            (
                self.assignment_1_completion_match_id is not None
                or self.assignment_1 is None
            )
            and (
                self.assignment_2_completion_match_id is not None
                or self.assignment_2 is None
            )
            and (
                self.assignment_3_completion_match_id is not None
                or self.assignment_3 is None
            )
        )
