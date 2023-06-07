# Generated by Django 4.1.1 on 2023-06-06 20:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discord", "0002_alter_discordaccount_options_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discordaccount",
            name="discord_username",
            field=models.CharField(
                max_length=32,
                validators=[django.core.validators.MinLengthValidator(2)],
                verbose_name="Discord Username",
            ),
        ),
    ]