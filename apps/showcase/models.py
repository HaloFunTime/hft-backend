from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.discord.models import DiscordAccount
from apps.overrides.models import Base


class ShowcaseFile(Base):
    class Meta:
        db_table = "ShowcaseFile"
        ordering = [
            "-created_at",
        ]
        verbose_name = "Showcase File"
        verbose_name_plural = "Showcase Files"

    class FileType(models.TextChoices):
        Map = "map", _("Map")
        Mode = "mode", _("Mode")
        Prefab = "prefab", _("Prefab")

    showcase_owner = models.ForeignKey(
        DiscordAccount,
        on_delete=models.RESTRICT,
        verbose_name="Showcase Owner",
        related_name="showcase_owners",
    )
    file_type = models.CharField(max_length=16, choices=FileType.choices)
    file_id = models.UUIDField(verbose_name="File ID")
    position = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    def __str__(self):
        return f"{str(self.showcase_owner)} File #{self.position} ({self.get_file_type_display()})"


class ShowcaseFileSnapshot(Base):
    class Meta:
        db_table = "ShowcaseFileSnapshot"
        ordering = [
            "-snapshot_date",
        ]
        verbose_name = "Showcase File Snapshot"
        verbose_name_plural = "Showcase File Snapshots"

    file = models.ForeignKey(
        ShowcaseFile,
        on_delete=models.CASCADE,
        verbose_name="Showcase File",
        related_name="snapshots",
    )
    version_id = models.UUIDField(verbose_name="Version ID")
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=512)
    snapshot_date = models.DateField()
    plays_recent = models.IntegerField()
    plays_all_time = models.IntegerField()
    favorites = models.IntegerField()
    number_of_ratings = models.IntegerField()
    average_rating = models.DecimalField(max_digits=16, decimal_places=15)

    def __str__(self):
        return self.name + ": " + self.snapshot_date
