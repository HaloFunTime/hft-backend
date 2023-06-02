# Generated by Django 4.1.1 on 2023-03-06 06:03

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
            name="TrailblazerVODReview",
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
                ("submission_date", models.DateField(verbose_name="Submission Date")),
                (
                    "submission_link",
                    models.CharField(
                        blank=True, max_length=512, verbose_name="Submission Link"
                    ),
                ),
                (
                    "submission_notes",
                    models.TextField(blank=True, verbose_name="Submission Notes"),
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
                    "submitter_discord",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="trailblazer_vod_submitters",
                        to="discord.discordaccount",
                        verbose_name="Submitter Discord",
                    ),
                ),
            ],
            options={
                "verbose_name": "VOD Review",
                "verbose_name_plural": "VOD Reviews",
                "db_table": "TrailblazerVODReview",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TrailblazerTuesdayReferral",
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
                ("referral_date", models.DateField(verbose_name="Referral Date")),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invitee_discord",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="trailblazer_tuesday_invitees",
                        to="discord.discordaccount",
                        verbose_name="Invitee Discord",
                    ),
                ),
                (
                    "referrer_discord",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="trailblazer_tuesday_referrers",
                        to="discord.discordaccount",
                        verbose_name="Referrer Discord",
                    ),
                ),
            ],
            options={
                "verbose_name": "Tuesday Referral",
                "verbose_name_plural": "Tuesday Referrals",
                "db_table": "TrailblazerTuesdayReferral",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TrailblazerTuesdayAttendance",
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
                ("attendance_date", models.DateField(verbose_name="Attendance Date")),
                (
                    "attendee_discord",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="trailblazer_tuesday_attendees",
                        to="discord.discordaccount",
                        verbose_name="Attendee Discord",
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
                "verbose_name": "Tuesday Attendance",
                "verbose_name_plural": "Tuesday Attendances",
                "db_table": "TrailblazerTuesdayAttendance",
                "ordering": ["-created_at"],
            },
        ),
    ]
