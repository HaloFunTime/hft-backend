from django.core.validators import MinLengthValidator
from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


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

    def __str__(self):
        return f"{self.participant}"
