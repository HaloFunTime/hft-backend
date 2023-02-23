import datetime

from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey


class HaloInfiniteBuildID(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteBuildID"
        ordering = [
            "created_at",
        ]
        verbose_name = "Build ID"
        verbose_name_plural = "Build IDs"

    build_date = models.DateTimeField(verbose_name="Build Date")
    build_id = models.CharField(
        primary_key=True, max_length=256, verbose_name="Build ID"
    )


class HaloInfiniteXSTSToken(Base):
    class Meta:
        db_table = "HaloInfiniteXSTSToken"
        ordering = [
            "created_at",
        ]
        verbose_name = "XSTS Token"
        verbose_name_plural = "XSTS Tokens"

    @property
    def expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.not_after

    issue_instant = models.DateTimeField()
    not_after = models.DateTimeField()
    token = models.TextField()
    uhs = models.CharField(max_length=64)


class HaloInfiniteSpartanToken(Base):
    class Meta:
        db_table = "HaloInfiniteSpartanToken"
        ordering = [
            "created_at",
        ]
        verbose_name = "Spartan Token"
        verbose_name_plural = "Spartan Tokens"

    @property
    def expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expires_utc

    expires_utc = models.DateTimeField()
    token = models.TextField()
    token_duration = models.CharField(max_length=64)


class HaloInfiniteClearanceToken(Base):
    class Meta:
        db_table = "HaloInfiniteClearanceToken"
        ordering = [
            "created_at",
        ]
        verbose_name = "Clearance Token"
        verbose_name_plural = "Clearance Tokens"

    flight_configuration_id = models.CharField(max_length=256)
