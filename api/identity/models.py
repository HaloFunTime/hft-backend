from django.db import models

from api.default.models import Base


class Identity(Base):
    class Meta:
        db_table = "Identity"

    # Discord IDs are uint64s:
    # https://discord.com/developers/docs/reference#snowflakes
    discord_id = models.CharField(max_length=64, unique=True)
    discord_username = models.CharField(max_length=32)
    discord_discriminator = models.CharField(max_length=4)
    # Xbox LIVE IDs (XUIDs) are uint64s:
    # https://docs.microsoft.com/en-us/gaming/gdk/_content/gc/reference/live/rest/uri/storage/uri-trustedplatformusersxuidscidssciddatapath-get
    xbox_id = models.CharField(max_length=64)
    xbox_gamertag = models.CharField(max_length=16, unique=True)
