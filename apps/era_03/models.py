from django.core.validators import MinValueValidator
from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class BoatRank(Base):
    class Meta:
        db_table = "BoatRank"
        ordering = ["tier", "track"]
        verbose_name = "Rank"
        verbose_name_plural = "Ranks"

    class Tracks(models.TextChoices):
        NA = "N/A", "N/A"
        COMMAND = "COMMAND", "Command"
        MACHINERY = "MACHINERY", "Machinery"
        HOSPITALITY = "HOSPITALITY", "Hospitality"
        CULINARY = "CULINARY", "Culinary"

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
