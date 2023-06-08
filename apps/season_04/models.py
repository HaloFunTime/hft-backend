from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


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
