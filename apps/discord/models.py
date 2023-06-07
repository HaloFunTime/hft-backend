from django.core.validators import MinLengthValidator
from django.db import models

from apps.overrides.models import BaseWithoutPrimaryKey


class DiscordAccount(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "DiscordAccount"
        ordering = [
            "discord_username",
        ]
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    discord_id = models.CharField(
        primary_key=True, max_length=20, blank=False, verbose_name="Discord User ID"
    )
    discord_username = models.CharField(
        max_length=37,
        blank=False,
        verbose_name="Discord Username",
        validators=[MinLengthValidator(2)],
    )

    def __str__(self):
        return self.discord_username
