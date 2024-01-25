# Generated by Django 5.0.1 on 2024-01-24 17:51

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("intern", "0008_internhikequeuequip"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InternPathfinderProdigyDemotionQuip",
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
                "verbose_name": "Pathfinder Prodigy Demotion Quip",
                "verbose_name_plural": "Pathfinder Prodigy Demotion Quips",
                "db_table": "InternPathfinderProdigyDemotionQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternPathfinderProdigyPromotionQuip",
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
                "verbose_name": "Pathfinder Prodigy Promotion Quip",
                "verbose_name_plural": "Pathfinder Prodigy Promotion Quips",
                "db_table": "InternPathfinderProdigyPromotionQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternTrailblazerTitanDemotionQuip",
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
                "verbose_name": "Trailblazer Titan Demotion Quip",
                "verbose_name_plural": "Trailblazer Titan Demotion Quips",
                "db_table": "InternTrailblazerTitanDemotionQuip",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.CreateModel(
            name="InternTrailblazerTitanPromotionQuip",
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
                "verbose_name": "Trailblazer Titan Promotion Quip",
                "verbose_name_plural": "Trailblazer Titan Promotion Quips",
                "db_table": "InternTrailblazerTitanPromotionQuip",
                "ordering": ["-updated_at"],
            },
        ),
    ]
