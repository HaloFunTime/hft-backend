from django.core.validators import MinLengthValidator
from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey


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


class DiscordLFGThreadHelpPrompt(Base):
    class Meta:
        db_table = "DiscordLFGThreadHelpPrompt"
        ordering = [
            "-created_at",
        ]
        verbose_name = "LFG Thread Help Prompt"
        verbose_name_plural = "LFG Thread Help Prompts"

    help_receiver_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Help Receiver Discord",
        related_name="lfg_thread_help_receivers",
    )
    lfg_thread_name = models.CharField(
        max_length=100, blank=False, verbose_name="LFG Thread Name"
    )
    lfg_thread_id = models.CharField(
        max_length=20, blank=False, verbose_name="LFG Thread ID"
    )

    def __str__(self):
        return f"{self.help_receiver_discord} in {self.lfg_thread_name}"
