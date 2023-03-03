import datetime

from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey


class XboxLiveAccount(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "XboxLiveAccount"
        ordering = [
            "gamertag",
        ]
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    gamertag = models.CharField(max_length=15)
    xuid = models.PositiveBigIntegerField(primary_key=True, verbose_name="Xbox Live ID")

    def __str__(self):
        return self.gamertag


class XboxLiveOAuthToken(Base):
    class Meta:
        db_table = "XboxLiveOAuthToken"
        ordering = [
            "-created_at",
        ]
        verbose_name = "OAuth Token"
        verbose_name_plural = "OAuth Tokens"

    @property
    def expiration_datetime(self) -> datetime.datetime:
        # Expiration datetime is calculated by adding "expires_in" seconds to
        # "created_at", less a small kludge factor to account for any latency
        # that occurred between generating the token and databasing it.
        return self.created_at + datetime.timedelta(seconds=(self.expires_in - 30))

    @property
    def expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.expiration_datetime

    token_type = models.CharField(max_length=64)
    expires_in = models.IntegerField()
    scope = models.CharField(max_length=256)
    access_token = models.TextField()
    refresh_token = models.TextField()
    user_id = models.CharField(max_length=64)


class XboxLiveUserToken(Base):
    class Meta:
        db_table = "XboxLiveUserToken"
        ordering = [
            "-created_at",
        ]
        verbose_name = "User Token"
        verbose_name_plural = "User Tokens"

    @property
    def expired(self) -> bool:
        return datetime.datetime.now(datetime.timezone.utc) > self.not_after

    issue_instant = models.DateTimeField()
    not_after = models.DateTimeField()
    token = models.TextField()
    uhs = models.CharField(max_length=64)


class XboxLiveXSTSToken(Base):
    class Meta:
        db_table = "XboxLiveXSTSToken"
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
