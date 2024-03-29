# Generated by Django 4.1.1 on 2023-02-23 05:10

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
            name="HaloInfiniteXSTSToken",
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
                ("issue_instant", models.DateTimeField()),
                ("not_after", models.DateTimeField()),
                ("token", models.TextField()),
                ("uhs", models.CharField(max_length=64)),
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
                "verbose_name": "XSTS Token",
                "verbose_name_plural": "XSTS Tokens",
                "db_table": "HaloInfiniteXSTSToken",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="HaloInfiniteSpartanToken",
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
                ("expires_utc", models.DateTimeField()),
                ("token", models.TextField()),
                ("token_duration", models.CharField(max_length=64)),
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
                "verbose_name": "Spartan Token",
                "verbose_name_plural": "Spartan Tokens",
                "db_table": "HaloInfiniteSpartanToken",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="HaloInfiniteClearanceToken",
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
                ("flight_configuration_id", models.CharField(max_length=256)),
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
                "verbose_name": "Clearance Token",
                "verbose_name_plural": "Clearance Tokens",
                "db_table": "HaloInfiniteClearanceToken",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="HaloInfiniteBuildID",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("build_date", models.DateTimeField(verbose_name="Build Date")),
                (
                    "build_id",
                    models.CharField(
                        max_length=256,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Build ID",
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
                "verbose_name": "Build ID",
                "verbose_name_plural": "Build IDs",
                "db_table": "HaloInfiniteBuildID",
                "ordering": ["created_at"],
            },
        ),
    ]
