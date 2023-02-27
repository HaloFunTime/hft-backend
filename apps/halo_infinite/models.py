import datetime

from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey

CLEARANCE_EXPIRATION_SECONDS = 900


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


class HaloInfinitePlaylist(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfinitePlaylist"
        ordering = [
            "created_at",
        ]
        verbose_name = "Playlist"
        verbose_name_plural = "Playlists"

    playlist_id = models.UUIDField(primary_key=True, verbose_name="Playlist ID")
    version_id = models.UUIDField(blank=True, verbose_name="Version ID")
    ranked = models.BooleanField()
    active = models.BooleanField(default=False)
    name = models.CharField(blank=True, max_length=256)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class HaloInfiniteSeason(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteSeason"
        ordering = [
            "created_at",
        ]
        verbose_name = "Season"
        verbose_name_plural = "Seasons"

    season_id = models.CharField(
        primary_key=True, max_length=256, verbose_name="Season ID"
    )
    name = models.CharField(max_length=256, verbose_name="Season Name")
    start_date = models.DateTimeField(verbose_name="Start Date & Time")
    end_date = models.DateTimeField(verbose_name="End Date & Time")

    def __str__(self):
        return self.name


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

    @property
    def expiration_datetime(self) -> datetime.datetime:
        # Expiration datetime is calculated by adding CLEARANCE_EXPIRATION_SECONDS to
        # "created_at", less a small kludge factor to account for any latency
        # that occurred between generating the token and databasing it.
        return self.created_at + datetime.timedelta(
            seconds=(CLEARANCE_EXPIRATION_SECONDS - 30)
        )

    @property
    def expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expiration_datetime

    flight_configuration_id = models.CharField(max_length=256)
