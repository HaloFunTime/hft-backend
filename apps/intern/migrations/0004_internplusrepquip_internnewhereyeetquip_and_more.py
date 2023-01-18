# Generated by Django 4.1.1 on 2023-01-17 22:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("intern", "0003_internhelpfulhint"),
    ]

    operations = [
        migrations.CreateModel(
            name="InternPlusRepQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Quip Text"
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
                "verbose_name": "Plus Rep Quip",
                "verbose_name_plural": "Plus Rep Quips",
                "db_table": "InternPlusRepQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternNewHereYeetQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Quip Text"
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
                "verbose_name": "New Here Yeet Quip",
                "verbose_name_plural": "New Here Yeet Quips",
                "db_table": "InternNewHereYeetQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternNewHereWelcomeQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Quip Text"
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
                "verbose_name": "New Here Welcome Quip",
                "verbose_name_plural": "New Here Welcome Quips",
                "db_table": "InternNewHereWelcomeQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternChatterPauseReverenceQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Quip Text"
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
                "verbose_name": "Chatter Pause Reverence Quip",
                "verbose_name_plural": "Chatter Pause Reverence Quips",
                "db_table": "InternChatterPauseReverenceQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternChatterPauseDenialQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Quip Text"
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
                "verbose_name": "Chatter Pause Denial Quip",
                "verbose_name_plural": "Chatter Pause Denial Quips",
                "db_table": "InternChatterPauseDenialQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternChatterPauseAcceptanceQuip",
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
                    "quip_text",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Quip Text"
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
                "verbose_name": "Chatter Pause Acceptance Quip",
                "verbose_name_plural": "Chatter Pause Acceptance Quips",
                "db_table": "InternChatterPauseAcceptanceQuip",
                "ordering": ["-updated_at"],
            },
        ),
    ]
