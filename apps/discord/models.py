from django.db import models

from apps.overrides.models import BaseWithoutPrimaryKey


class DiscordAccount(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "DiscordAccount"
        ordering = [
            "discord_tag",
        ]
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    discord_id = models.CharField(
        primary_key=True, max_length=20, blank=False, verbose_name="Discord User ID"
    )
    discord_tag = models.CharField(
        max_length=37, blank=False, verbose_name="Discord User Tag"
    )

    def __str__(self):
        return self.discord_tag
