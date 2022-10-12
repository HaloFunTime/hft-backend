# Generated by Django 4.1.1 on 2022-09-28 07:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SeriesMode",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=32)),
                (
                    "hi_asset_id",
                    models.CharField(
                        blank=True, max_length=36, verbose_name="Halo Infinite Asset ID"
                    ),
                ),
                (
                    "hi_version_id",
                    models.CharField(
                        blank=True,
                        max_length=36,
                        verbose_name="Halo Infinite Version ID",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Series Mode",
                "verbose_name_plural": "Series Modes",
                "db_table": "SeriesMode",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="SeriesRuleset",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.CharField(
                        max_length=255, primary_key=True, serialize=False, unique=True
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                (
                    "allow_bo3_map_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Map Repeats in Best of 3?"
                    ),
                ),
                (
                    "allow_bo3_mode_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Mode Repeats in Best of 3?"
                    ),
                ),
                (
                    "allow_bo5_map_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Map Repeats in Best of 5?"
                    ),
                ),
                (
                    "allow_bo5_mode_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Mode Repeats in Best of 5?"
                    ),
                ),
                (
                    "allow_bo7_map_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Map Repeats in Best of 7?"
                    ),
                ),
                (
                    "allow_bo7_mode_repeats",
                    models.BooleanField(
                        default=False, verbose_name="Allow Mode Repeats in Best of 7?"
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "featured_mode",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="series.seriesmode",
                        verbose_name="Featured Mode",
                    ),
                ),
            ],
            options={
                "verbose_name": "Series Ruleset",
                "verbose_name_plural": "Series Rulesets",
                "db_table": "SeriesRuleset",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="SeriesMap",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=32)),
                (
                    "hi_asset_id",
                    models.CharField(
                        blank=True, max_length=36, verbose_name="Halo Infinite Asset ID"
                    ),
                ),
                (
                    "hi_version_id",
                    models.CharField(
                        blank=True,
                        max_length=36,
                        verbose_name="Halo Infinite Version ID",
                    ),
                ),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Series Map",
                "verbose_name_plural": "Series Maps",
                "db_table": "SeriesMap",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="SeriesGametype",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "map",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="series.seriesmap",
                    ),
                ),
                (
                    "mode",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="series.seriesmode",
                    ),
                ),
                (
                    "ruleset",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="series.seriesruleset",
                    ),
                ),
            ],
            options={
                "verbose_name": "Series Gametype",
                "verbose_name_plural": "Series Gametypes",
                "db_table": "SeriesGametype",
                "ordering": ["-updated_at"],
            },
        ),
    ]