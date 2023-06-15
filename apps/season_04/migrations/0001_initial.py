# Generated by Django 4.1.1 on 2023-06-08 04:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("discord", "0003_alter_discordaccount_discord_username"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="StampChampEarner",
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
                ("earned_at", models.DateTimeField()),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "earner",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.RESTRICT,
                        related_name="stamp_champ_earner",
                        to="discord.discordaccount",
                    ),
                ),
            ],
            options={
                "verbose_name": "Stamp Champ Earner",
                "verbose_name_plural": "Stamp Champ Earners",
                "db_table": "StampChampEarner",
                "ordering": ["-created_at"],
            },
        ),
    ]