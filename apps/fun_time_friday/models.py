from django.db import models

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class FunTimeFridayVoiceConnect(Base):
    class Meta:
        db_table = "FunTimeFridayVoiceConnect"
        ordering = ["-connected_at"]
        verbose_name = "Voice Connect"
        verbose_name_plural = "Voice Connects"

    connector_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="connectors",
        verbose_name="Connector Discord",
    )
    connected_at = models.DateTimeField(verbose_name="Connected At")
    channel_id = models.CharField(max_length=20, blank=False, verbose_name="Channel ID")
    channel_name = models.CharField(
        max_length=50, blank=True, verbose_name="Channel Name"
    )

    def __str__(self):
        return f"{str(self.connector_discord)} connected"


class FunTimeFridayVoiceDisconnect(Base):
    class Meta:
        db_table = "FunTimeFridayVoiceDisconnect"
        ordering = ["-disconnected_at"]
        verbose_name = "Voice Disconnect"
        verbose_name_plural = "Voice Disconnects"

    disconnector_discord = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        related_name="disconnectors",
        verbose_name="Disconnector Discord",
    )
    disconnected_at = models.DateTimeField(verbose_name="Disconnected At")
    channel_id = models.CharField(max_length=20, blank=False, verbose_name="Channel ID")
    channel_name = models.CharField(
        max_length=50, blank=True, verbose_name="Channel Name"
    )

    def __str__(self):
        return f"{str(self.disconnector_discord)} disconnected"
