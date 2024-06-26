# Generated by Django 5.0.6 on 2024-06-05 18:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("era_02", "0004_alter_teamupchallengecompletion_challenge"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mvt",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="mvt",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="teamupchallengecompletion",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="teamupchallengecompletion",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
    ]
