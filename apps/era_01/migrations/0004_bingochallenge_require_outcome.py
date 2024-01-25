# Generated by Django 5.0.1 on 2024-01-15 22:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("era_01", "0003_bingochallenge_bingochallengecompletion"),
    ]

    operations = [
        migrations.AddField(
            model_name="bingochallenge",
            name="require_outcome",
            field=models.IntegerField(
                blank=True,
                choices=[(2, "Win"), (3, "Loss"), (1, "Tie"), (4, "Left")],
                null=True,
                verbose_name="Outcome",
            ),
        ),
    ]