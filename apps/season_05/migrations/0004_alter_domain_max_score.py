# Generated by Django 4.1.1 on 2023-10-20 05:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("season_05", "0003_alter_domain_max_score_alter_domain_stat"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="max_score",
            field=models.IntegerField(verbose_name="Max Score"),
        ),
    ]
