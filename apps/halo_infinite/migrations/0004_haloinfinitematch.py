# Generated by Django 5.0.1 on 2024-01-10 00:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("halo_infinite", "0003_alter_haloinfinitebuildid_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="HaloInfiniteMatch",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "match_id",
                    models.UUIDField(
                        primary_key=True, serialize=False, verbose_name="Match ID"
                    ),
                ),
                (
                    "start_time",
                    models.DateTimeField(blank=True, verbose_name="Start Time"),
                ),
                ("end_time", models.DateTimeField(blank=True, verbose_name="End Time")),
                (
                    "data",
                    models.JSONField(blank=True, default=dict, verbose_name="Raw Data"),
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
                "verbose_name": "Match",
                "verbose_name_plural": "Matches",
                "db_table": "HaloInfiniteMatch",
                "ordering": ["-end_time"],
            },
        ),
    ]
