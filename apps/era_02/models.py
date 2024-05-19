from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from apps.discord.models import DiscordAccount
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.overrides.models import Base


class TeamUpChallenges(models.TextChoices):
    BAIT_THE_FLAGS = "BAIT_THE_FLAGS", _("Bait the Flags")
    FORTY_FISTS = "FORTY_FISTS", _("Forty Fists")
    GRENADE_PARADE = "GRENADE_PARADE", _("Grenade Parade")
    HUNDRED_HEADS = "HUNDRED_HEADS", _("Hundred Heads")
    MOST_VALUABLE_DRIVER = "MOST_VALUABLE_DRIVER", _("Most Valuable Driver")
    OWN_THE_ZONES = "OWN_THE_ZONES", _("Own the Zones")
    SPEED_FOR_SEEDS = "SPEED_FOR_SEEDS", _("Speed for Seeds")
    SPIN_CLASS = "SPIN_CLASS", _("Spin Class")
    STICKY_ICKY = "STICKY_ICKY", _("Sticky Icky")
    SUMMON_A_DEMON = "SUMMON_A_DEMON", _("Summon a Demon")


class MVT(Base):
    class Meta:
        db_table = "MVT"
        ordering = ["-created_at"]
        verbose_name = "MVT"
        verbose_name_plural = "MVTs"

    earner = models.OneToOneField(
        DiscordAccount, on_delete=models.RESTRICT, related_name="mvt"
    )
    earned_at = models.DateTimeField()
    mvt_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.earner} ({self.earned_at})"


class TeamUpChallengeCompletion(Base):
    class Meta:
        db_table = "TeamUpChallengeCompletion"
        ordering = ["-created_at"]
        verbose_name = "Challenge Completion"
        verbose_name_plural = "Challenge Completions"

    match = models.ForeignKey(
        HaloInfiniteMatch,
        on_delete=models.CASCADE,
        related_name="+",
    )
    challenge = models.CharField(choices=TeamUpChallenges.choices)
    xuid = models.PositiveBigIntegerField(verbose_name="Xbox Live ID")
    score = models.CharField()

    @property
    def external_match_link(self):
        return (
            ""
            if self.match_id is None
            else format_html(
                f"<a href=https://halotracker.com/halo-infinite/match/{self.match_id}>View on HaloTracker</a>"
            )
        )
