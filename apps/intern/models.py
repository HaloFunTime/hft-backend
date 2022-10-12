from django.db import models

from apps.overrides.models import Base


class InternChatter(Base):
    class Meta:
        db_table = "InternChatter"
        ordering = ["-updated_at"]
        verbose_name = "Chatter"
        verbose_name_plural = "Chatters"

    message_text = models.TextField(
        max_length=2000, blank=True, verbose_name="Message Text"
    )

    @property
    def short_message_text(self):
        return (
            (self.message_text[:50] + "...")
            if len(self.message_text) > 50
            else self.message_text
        )

    def __str__(self):
        return self.short_message_text


class InternChatterForbiddenChannel(Base):
    class Meta:
        db_table = "InternChatterForbiddenChannel"
        ordering = ["-updated_at"]
        verbose_name = "Forbidden Channel"
        verbose_name_plural = "Forbidden Channels"

    discord_channel_id = models.CharField(
        max_length=32, unique=True, verbose_name="Discord Channel ID"
    )
    discord_channel_name = models.TextField(
        blank=True, verbose_name="Discord Channel Name"
    )

    def __str__(self):
        return str(self.discord_channel_id)


class InternChatterPause(Base):
    class Meta:
        db_table = "InternChatterPause"
        ordering = ["-created_at"]
        verbose_name = "Pause"
        verbose_name_plural = "Pauses"

    discord_user_id = models.CharField(max_length=32, verbose_name="Discord User ID")
    discord_user_tag = models.CharField(
        max_length=40, blank=True, verbose_name="Discord Username"
    )

    def __str__(self):
        return str(self.created_at)
