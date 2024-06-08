import datetime

from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey

CLEARANCE_EXPIRATION_SECONDS = 900


class HaloInfiniteBuildID(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteBuildID"
        ordering = [
            "-created_at",
        ]
        verbose_name = "Build ID"
        verbose_name_plural = "Build IDs"

    build_date = models.DateTimeField(verbose_name="Build Date")
    build_id = models.CharField(
        primary_key=True, max_length=256, verbose_name="Build ID"
    )


class HaloInfiniteMatch(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteMatch"
        ordering = [
            "-end_time",
        ]
        verbose_name = "Match"
        verbose_name_plural = "Matches"

    match_id = models.UUIDField(primary_key=True, verbose_name="Match ID")
    start_time = models.DateTimeField(blank=True, verbose_name="Start Time")
    end_time = models.DateTimeField(blank=True, verbose_name="End Time")
    data = models.JSONField(blank=True, default=dict, verbose_name="Raw Data")

    def __str__(self):
        return str(self.match_id)


class HaloInfiniteMap(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteMap"
        ordering = [
            "-published_at",
        ]
        verbose_name = "Map"
        verbose_name_plural = "Maps"

    asset_id = models.UUIDField(primary_key=True, verbose_name="Asset ID")
    version_id = models.UUIDField(blank=True, verbose_name="Version ID")
    public_name = models.CharField(blank=True, max_length=255, verbose_name="Name")
    description = models.CharField(
        blank=True, max_length=255, verbose_name="Description"
    )
    published_at = models.DateTimeField(blank=True, verbose_name="Published Time")
    data = models.JSONField(blank=True, default=dict, verbose_name="Raw Data")

    def __str__(self):
        return (
            f"{self.public_name} ({self.published_at.strftime('%Y-%m-%dT%H:%M:%SZ')})"
        )


class HaloInfiniteMapModePair(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfiniteMapModePair"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "MapModePair"
        verbose_name_plural = "MapModePairs"

    asset_id = models.UUIDField(primary_key=True, verbose_name="Asset ID")
    version_id = models.UUIDField(blank=True, verbose_name="Version ID")
    public_name = models.CharField(blank=True, max_length=255, verbose_name="Name")
    description = models.CharField(
        blank=True, max_length=255, verbose_name="Description"
    )
    data = models.JSONField(blank=True, default=dict, verbose_name="Raw Data")

    def __str__(self):
        return self.public_name


class HaloInfinitePlaylist(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "HaloInfinitePlaylist"
        ordering = [
            "-active",
            "name",
        ]
        verbose_name = "Playlist"
        verbose_name_plural = "Playlists"

    playlist_id = models.UUIDField(primary_key=True, verbose_name="Playlist ID")
    version_id = models.UUIDField(blank=True, verbose_name="Version ID")
    ranked = models.BooleanField()
    active = models.BooleanField(default=False)
    name = models.CharField(blank=True, max_length=256)
    description = models.TextField(blank=True)
    info = models.JSONField(blank=True, default=dict, verbose_name="Raw Info")
    data = models.JSONField(blank=True, default=dict, verbose_name="Raw Data")

    def __str__(self):
        return self.name


class HaloInfiniteXSTSToken(Base):
    class Meta:
        db_table = "HaloInfiniteXSTSToken"
        ordering = [
            "-created_at",
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
            "-created_at",
        ]
        verbose_name = "Spartan Token"
        verbose_name_plural = "Spartan Tokens"

    @property
    def expired(self) -> bool:
        # Expired property returns True 15 seconds early to account for latency
        return datetime.datetime.now(datetime.timezone.utc) > (
            self.expires_utc - datetime.timedelta(seconds=15)
        )

    expires_utc = models.DateTimeField()
    token = models.TextField()
    token_duration = models.CharField(max_length=64)


class HaloInfiniteClearanceToken(Base):
    class Meta:
        db_table = "HaloInfiniteClearanceToken"
        ordering = [
            "-created_at",
        ]
        verbose_name = "Clearance Token"
        verbose_name_plural = "Clearance Tokens"

    @property
    def expiration_datetime(self) -> datetime.datetime:
        # Expiration datetime is calculated by adding CLEARANCE_EXPIRATION_SECONDS to
        # "created_at", less a small kludge factor to account for any latency
        # that occurred between generating the token and databasing it.
        return self.created_at + datetime.timedelta(
            seconds=(CLEARANCE_EXPIRATION_SECONDS - 15)
        )

    @property
    def expired(self) -> bool:
        # Expired property returns True 15 seconds early to account for latency
        return datetime.datetime.now(datetime.timezone.utc) > (
            self.expiration_datetime - datetime.timedelta(seconds=15)
        )

    flight_configuration_id = models.CharField(max_length=256)
