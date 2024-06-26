# Generated by Django 5.0.6 on 2024-05-26 04:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("era_02", "0003_teamupchallengecompletion_score_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="teamupchallengecompletion",
            name="challenge",
            field=models.CharField(
                choices=[
                    ("BAIT_THE_FLAGS", "Bait the Flags"),
                    ("FORTY_FISTS", "Forty Fists"),
                    ("GRENADE_PARADE", "Grenade Parade"),
                    ("HUNDRED_HEADS", "Hundred Heads"),
                    ("MARKS_OF_SHAME", "Marks of Shame"),
                    ("MOST_VALUABLE_DRIVER", "Most Valuable Driver"),
                    ("OWN_THE_ZONES", "Own the Zones"),
                    ("SPEED_FOR_SEEDS", "Speed for Seeds"),
                    ("SPIN_CLASS", "Spin Class"),
                    ("SUMMON_A_DEMON", "Summon a Demon"),
                ]
            ),
        ),
    ]
