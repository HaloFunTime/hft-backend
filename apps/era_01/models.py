from django.core.validators import MinLengthValidator
from django.db import models

from apps.discord.models import DiscordAccount
from apps.halo_infinite.constants import STATS
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.overrides.models import Base, BaseWithoutPrimaryKey


def get_stat_choices():
    choices = []
    for key in STATS:
        choices.append(
            (key, f"{key.split('_')[0].rstrip('Stats')}: {STATS.get(key)[1]}")
        )
    return choices


class BingoBuff(Base):
    class Meta:
        db_table = "BingoBuff"
        ordering = ["-created_at"]
        verbose_name = "Bingo Buff"
        verbose_name_plural = "Bingo Buffs"

    earner = models.OneToOneField(
        DiscordAccount, on_delete=models.RESTRICT, related_name="bingo_buff"
    )
    earned_at = models.DateTimeField()
    bingo_count = models.IntegerField(default=0)
    challenge_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.earner} ({self.earned_at})"


class BingoChallengeParticipant(Base):
    class Meta:
        db_table = "BingoChallengeParticipant"
        ordering = ["-created_at"]
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    participant = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="bingo_participants",
        verbose_name="Participant",
    )
    board_order = models.CharField(
        max_length=25, validators=[MinLengthValidator(25)], verbose_name="Board Order"
    )
    most_recent_match_id = models.UUIDField(
        null=True, blank=True, verbose_name="Most Recent Match ID"
    )

    def __str__(self):
        return f"{self.participant}"


class BingoChallenge(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "BingoChallenge"
        ordering = ["id"]
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

    class LifecycleMode(models.IntegerChoices):
        CUSTOM = 1
        MATCHMADE = 3

    class Outcome(models.IntegerChoices):
        WIN = 2
        LOSS = 3
        TIE = 1
        LEFT = 4

    id = models.CharField(primary_key=True, max_length=1, verbose_name="ID")
    name = models.CharField(max_length=128, verbose_name="Name")
    description = models.CharField(max_length=256, verbose_name="Description")
    require_match_type = models.IntegerField(
        blank=True,
        null=True,
        choices=LifecycleMode.choices,
        verbose_name="Match Type",
    )
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
    require_present_at_beginning = models.BooleanField(
        blank=True, null=True, verbose_name="Present at Game Start"
    )
    require_present_at_completion = models.BooleanField(
        blank=True, null=True, verbose_name="Present at Game End"
    )
    stat = models.CharField(
        max_length=128, choices=get_stat_choices, verbose_name="Stat"
    )
    medal_id = models.DecimalField(
        decimal_places=0,
        max_digits=15,
        verbose_name="Medal ID (only necessary if Stat is 'Medals')",
        blank=True,
        null=True,
    )
    score = models.CharField(max_length=128, verbose_name="Score")

    def __str__(self):
        return f"{self.id} - {self.name}"


class BingoChallengeCompletion(Base):
    class Meta:
        db_table = "BingoChallengeCompletion"
        ordering = ["-created_at"]
        verbose_name = "Challenge Completion"
        verbose_name_plural = "Challenge Completions"

    challenge = models.ForeignKey(
        BingoChallenge,
        on_delete=models.RESTRICT,
        related_name="completions",
        verbose_name="Completion",
    )
    participant = models.ForeignKey(
        BingoChallengeParticipant,
        on_delete=models.RESTRICT,
        related_name="completions",
        verbose_name="Completion",
    )
    match = models.ForeignKey(
        HaloInfiniteMatch,
        on_delete=models.RESTRICT,
        related_name="completions",
        verbose_name="Completion",
    )
