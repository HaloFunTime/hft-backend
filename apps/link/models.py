from django.conf import settings
from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base
from apps.xbox_live.models import XboxLiveAccount


class DiscordXboxLiveLink(Base):
    class Meta:
        db_table = "DiscordXboxLiveLink"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "Discord <-> Xbox Live Link"
        verbose_name_plural = "Discord <-> Xbox Live Links"

    def __str__(self):
        return f"{str(self.discord_account)} <-> {str(self.xbox_live_account)}"

    discord_account = models.OneToOneField(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Discord Account",
    )
    xbox_live_account = models.OneToOneField(
        XboxLiveAccount,
        on_delete=models.RESTRICT,
        verbose_name="Xbox Live Account",
    )
    verified = models.BooleanField(default=False, verbose_name="Verified?")
    verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        default=None,
        null=True,
        on_delete=models.RESTRICT,
        related_name="verifiers",
    )
