from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class PlusRep(Base):
    class Meta:
        db_table = "PlusRep"
        ordering = ["-updated_at"]
        verbose_name = "Plus Rep"
        verbose_name_plural = "Plus Reps"

    giver = models.ForeignKey(
        DiscordAccount, on_delete=models.RESTRICT, related_name="givers"
    )
    receiver = models.ForeignKey(
        DiscordAccount, on_delete=models.RESTRICT, related_name="receivers"
    )
    message = models.TextField(blank=True, verbose_name="Message")

    @property
    def short_message(self):
        return (self.message[:50] + "...") if len(self.message) > 50 else self.message

    def __str__(self):
        return self.short_message
