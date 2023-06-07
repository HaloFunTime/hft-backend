# Generated by Django 4.1.1 on 2023-02-14 06:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("xbox_live", "0002_alter_xboxliveaccount_options"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="xboxliveaccount",
            name="id",
        ),
        migrations.AddField(
            model_name="xboxliveaccount",
            name="xuid",
            field=models.PositiveBigIntegerField(
                default=0,
                primary_key=True,
                serialize=False,
                verbose_name="Xbox Live ID",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="xboxliveaccount",
            name="gamertag",
            field=models.CharField(max_length=15),
        ),
        migrations.CreateModel(
            name="XboxLiveXSTSToken",
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
                "verbose_name": "XSTSToken",
                "verbose_name_plural": "XSTSTokens",
                "db_table": "XboxLiveXSTSToken",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="XboxLiveUserToken",
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
                "verbose_name": "UserToken",
                "verbose_name_plural": "UserTokens",
                "db_table": "XboxLiveUserToken",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="XboxLiveOAuthToken",
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
                ("token_type", models.CharField(max_length=64)),
                ("expires_in", models.IntegerField()),
                ("scope", models.CharField(max_length=256)),
                ("access_token", models.TextField()),
                ("refresh_token", models.TextField()),
                ("user_id", models.CharField(max_length=64)),
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
                "verbose_name": "OAuthToken",
                "verbose_name_plural": "OAuthTokens",
                "db_table": "XboxLiveOAuthToken",
                "ordering": ["created_at"],
            },
        ),
    ]
