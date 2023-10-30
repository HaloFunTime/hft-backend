from django.db import models

from apps.discord.models import DiscordAccount
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
        verbose_name = "Chatter Forbidden Channel"
        verbose_name_plural = "Chatter Forbidden Channels"

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
        verbose_name = "Chatter Pause"
        verbose_name_plural = "Chatter Pauses"

    pauser = models.ForeignKey(
        DiscordAccount, on_delete=models.RESTRICT, related_name="pausers", null=True
    )

    def __str__(self):
        return str(self.created_at)


class InternChatterPauseAcceptanceQuip(Base):
    class Meta:
        db_table = "InternChatterPauseAcceptanceQuip"
        ordering = ["-updated_at"]
        verbose_name = "Chatter Pause Acceptance Quip"
        verbose_name_plural = "Chatter Pause Acceptance Quips"

    quip_text = models.CharField(max_length=100, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternChatterPauseDenialQuip(Base):
    class Meta:
        db_table = "InternChatterPauseDenialQuip"
        ordering = ["-updated_at"]
        verbose_name = "Chatter Pause Denial Quip"
        verbose_name_plural = "Chatter Pause Denial Quips"

    quip_text = models.CharField(max_length=100, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternChatterPauseReverenceQuip(Base):
    class Meta:
        db_table = "InternChatterPauseReverenceQuip"
        ordering = ["-updated_at"]
        verbose_name = "Chatter Pause Reverence Quip"
        verbose_name_plural = "Chatter Pause Reverence Quips"

    quip_text = models.CharField(max_length=100, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternHelpfulHint(Base):
    class Meta:
        db_table = "InternHelpfulHint"
        ordering = ["-updated_at"]
        verbose_name = "Helpful Hint"
        verbose_name_plural = "Helpful Hints"

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


class InternHikeQueueQuip(Base):
    class Meta:
        db_table = "InternHikeQueueQuip"
        ordering = ["-updated_at"]
        verbose_name = "Hike Queue Quip"
        verbose_name_plural = "Hike Queue Quips"

    quip_text = models.CharField(max_length=200, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternNewHereWelcomeQuip(Base):
    class Meta:
        db_table = "InternNewHereWelcomeQuip"
        ordering = ["-updated_at"]
        verbose_name = "New Here Welcome Quip"
        verbose_name_plural = "New Here Welcome Quips"

    quip_text = models.CharField(max_length=100, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternNewHereYeetQuip(Base):
    class Meta:
        db_table = "InternNewHereYeetQuip"
        ordering = ["-updated_at"]
        verbose_name = "New Here Yeet Quip"
        verbose_name_plural = "New Here Yeet Quips"

    quip_text = models.CharField(max_length=100, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternPassionReportQuip(Base):
    class Meta:
        db_table = "InternPassionReportQuip"
        ordering = ["-updated_at"]
        verbose_name = "Passion Report Quip"
        verbose_name_plural = "Passion Report Quips"

    quip_text = models.CharField(max_length=200, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text


class InternPlusRepQuip(Base):
    class Meta:
        db_table = "InternPlusRepQuip"
        ordering = ["-updated_at"]
        verbose_name = "Plus Rep Quip"
        verbose_name_plural = "Plus Rep Quips"

    quip_text = models.CharField(max_length=200, blank=True, verbose_name="Quip Text")

    @property
    def short_quip_text(self):
        return (
            (self.quip_text[:50] + "...")
            if len(self.quip_text) > 50
            else self.quip_text
        )

    def __str__(self):
        return self.short_quip_text
