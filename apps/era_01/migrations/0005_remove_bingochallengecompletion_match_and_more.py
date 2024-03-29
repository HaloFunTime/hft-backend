# Generated by Django 5.0.1 on 2024-01-26 04:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("era_01", "0004_bingochallenge_require_outcome"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="bingochallengecompletion",
            name="match",
        ),
        migrations.AddField(
            model_name="bingochallengecompletion",
            name="match_id",
            field=models.UUIDField(null=True, verbose_name="Match ID"),
        ),
        migrations.AlterField(
            model_name="bingochallengecompletion",
            name="challenge",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="completions",
                to="era_01.bingochallenge",
                verbose_name="Challenge",
            ),
        ),
        migrations.AlterField(
            model_name="bingochallengecompletion",
            name="participant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.RESTRICT,
                related_name="completions",
                to="era_01.bingochallengeparticipant",
                verbose_name="Participant",
            ),
        ),
    ]
