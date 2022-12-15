from django.db import models

from apps.overrides.models import Base, BaseWithoutPrimaryKey


class SeriesMap(Base):
    class Meta:
        db_table = "SeriesMap"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "Series Map"
        verbose_name_plural = "Series Maps"

    name = models.CharField(max_length=32)
    hi_asset_id = models.CharField(
        max_length=36, blank=True, verbose_name="Halo Infinite Asset ID"
    )
    hi_version_id = models.CharField(
        max_length=36, blank=True, verbose_name="Halo Infinite Version ID"
    )

    def __str__(self):
        return self.name


class SeriesMode(Base):
    class Meta:
        db_table = "SeriesMode"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "Series Mode"
        verbose_name_plural = "Series Modes"

    name = models.CharField(max_length=32)
    hi_asset_id = models.CharField(
        max_length=36, blank=True, verbose_name="Halo Infinite Asset ID"
    )
    hi_version_id = models.CharField(
        max_length=36, blank=True, verbose_name="Halo Infinite Version ID"
    )

    def __str__(self):
        return self.name


class SeriesRuleset(BaseWithoutPrimaryKey):
    class Meta:
        db_table = "SeriesRuleset"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "Series Ruleset"
        verbose_name_plural = "Series Rulesets"

    def __str__(self):
        return self.name

    id = models.CharField(max_length=32, primary_key=True, unique=True)
    name = models.CharField(max_length=255)
    featured_mode = models.ForeignKey(
        SeriesMode,
        on_delete=models.RESTRICT,
        blank=True,
        null=True,
        verbose_name="Featured Mode",
    )
    allow_bo3_map_repeats = models.BooleanField(
        default=False, verbose_name="Allow Map Repeats in Best of 3?"
    )
    allow_bo3_mode_repeats = models.BooleanField(
        default=False, verbose_name="Allow Mode Repeats in Best of 3?"
    )
    allow_bo5_map_repeats = models.BooleanField(
        default=False, verbose_name="Allow Map Repeats in Best of 5?"
    )
    allow_bo5_mode_repeats = models.BooleanField(
        default=False, verbose_name="Allow Mode Repeats in Best of 5?"
    )
    allow_bo7_map_repeats = models.BooleanField(
        default=False, verbose_name="Allow Map Repeats in Best of 7?"
    )
    allow_bo7_mode_repeats = models.BooleanField(
        default=False, verbose_name="Allow Mode Repeats in Best of 7?"
    )


class SeriesGametype(Base):
    class Meta:
        db_table = "SeriesGametype"
        ordering = [
            "-updated_at",
        ]
        verbose_name = "Series Gametype"
        verbose_name_plural = "Series Gametypes"

    ruleset = models.ForeignKey(SeriesRuleset, on_delete=models.CASCADE)
    map = models.ForeignKey(SeriesMap, on_delete=models.RESTRICT)
    mode = models.ForeignKey(SeriesMode, on_delete=models.RESTRICT)

    def __str__(self):
        return f"{self.ruleset}: {self.mode} on {self.map}"
