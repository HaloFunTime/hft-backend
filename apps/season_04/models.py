from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base, BaseWithoutPrimaryKey


class StampChallengeBTBMatch(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "StampChallengeBTBMatch"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge BTB Match"
        verbose_name_plural = "Stamp Challenge BTB Matches"

    class Challenges(models.TextChoices):
        FinishInFive = "16", _("Finish in Five")
        VictoryLap = "17", _("Victory Lap")
        TypeA = "18", _("Type A")
        FormerlyChucks = "19", _("Formerly Chuck's")
        InParticular = "20", _("In Particular")

    challenge = models.CharField(max_length=2, choices=Challenges.choices)
    match_id = models.UUIDField(primary_key=True, verbose_name="Match ID")

    @property
    def match_link(self):
        return format_html(
            f"<a href=https://halotracker.com/halo-infinite/match/{self.match_id}>View on HaloTracker</a>"
        )

    def __str__(self):
        return self.get_challenge_display() + " on " + str(self.created_at)


class StampChallenge16Completion(Base):
    class Meta:
        db_table = "StampChallenge16Completion"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge Completion: Finish in Five"
        verbose_name_plural = "Stamp Challenge Completions: Finish in Five"

    match = models.ForeignKey(StampChallengeBTBMatch, on_delete=models.CASCADE)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class StampChallenge17Completion(Base):
    class Meta:
        db_table = "StampChallenge17Completion"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge Completion: Victory Lap"
        verbose_name_plural = "Stamp Challenge Completions: Victory Lap"

    match = models.ForeignKey(StampChallengeBTBMatch, on_delete=models.CASCADE)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class StampChallenge18Completion(Base):
    class Meta:
        db_table = "StampChallenge18Completion"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge Completion: Type A"
        verbose_name_plural = "Stamp Challenge Completions: Type A"

    match = models.ForeignKey(StampChallengeBTBMatch, on_delete=models.CASCADE)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class StampChallenge19Completion(Base):
    class Meta:
        db_table = "StampChallenge19Completion"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge Completion: Formerly Chuck's"
        verbose_name_plural = "Stamp Challenge Completions: Formerly Chuck's"

    match = models.ForeignKey(StampChallengeBTBMatch, on_delete=models.CASCADE)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class StampChallenge20Completion(Base):
    class Meta:
        db_table = "StampChallenge20Completion"
        ordering = ["-created_at"]
        verbose_name = "Stamp Challenge Completion: In Particular"
        verbose_name_plural = "Stamp Challenge Completions: In Particular"

    match = models.ForeignKey(StampChallengeBTBMatch, on_delete=models.CASCADE)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")


class StampChampEarner(Base):
    class Meta:
        db_table = "StampChampEarner"
        ordering = ["-created_at"]
        verbose_name = "Stamp Champ Earner"
        verbose_name_plural = "Stamp Champ Earners"

    earner = models.OneToOneField(
        DiscordAccount, on_delete=models.RESTRICT, related_name="stamp_champ_earner"
    )
    earned_at = models.DateTimeField()

    def __str__(self):
        return str(self.earner) + " earned on " + str(self.earned_at)
