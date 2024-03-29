# Generated by Django 4.1.1 on 2023-03-05 22:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("discord", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PathfinderHikeSubmission",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "waywo_post_title",
                    models.CharField(max_length=100, verbose_name="WAYWO Post Title"),
                ),
                (
                    "waywo_post_id",
                    models.CharField(max_length=20, verbose_name="WAYWO Post ID"),
                ),
                (
                    "scheduled_playtest_date",
                    models.DateField(verbose_name="Scheduled Playtest Date"),
                ),
                ("map", models.CharField(max_length=32, verbose_name="Map")),
                ("mode_1", models.CharField(max_length=32, verbose_name="Mode 1")),
                ("mode_2", models.CharField(max_length=32, verbose_name="Mode 2")),
                (
                    "mode_1_played",
                    models.BooleanField(
                        default=False, verbose_name="Was Mode 1 played?"
                    ),
                ),
                (
                    "mode_2_played",
                    models.BooleanField(
                        default=False, verbose_name="Was Mode 2 played?"
                    ),
                ),
                (
                    "submitter_present_for_playtest",
                    models.BooleanField(
                        default=False,
                        verbose_name="Was the map submitter present for the playtest?",
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
                    "map_submitter_discord",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        to="discord.discordaccount",
                        verbose_name="Map Submitter Discord",
                    ),
                ),
            ],
            options={
                "verbose_name": "Hike Submission",
                "verbose_name_plural": "Hike Submissions",
                "db_table": "PathfinderHikeSubmission",
                "ordering": ["-scheduled_playtest_date", "-created_at"],
            },
        ),
    ]
