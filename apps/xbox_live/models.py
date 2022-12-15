from django.db import models

from apps.overrides.models import Base


class XboxLiveAccount(Base):
    class Meta:
        db_table = "XboxLiveAccount"
        ordering = [
            "gamertag",
        ]
        verbose_name = "Account"
        verbose_name_plural = "Accounts"

    gamertag = models.CharField(max_length=15, unique=True)
    # TODO: Create the `xuid` field once we have a way of computing it from the gamertag string, then switch the class
    # to extend BaseWithoutPrimaryKey. A custom migration to hydrate `xuid` will be necessary.
    # xuid = models.CharField(primary_key=True, max_length=20, verbose_name="Xbox Live ID")

    def __str__(self):
        return self.gamertag
