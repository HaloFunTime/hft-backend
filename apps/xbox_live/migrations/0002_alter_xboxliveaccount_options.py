# Generated by Django 4.1.1 on 2022-11-29 06:32

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("xbox_live", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="xboxliveaccount",
            options={
                "ordering": ["gamertag"],
                "verbose_name": "Account",
                "verbose_name_plural": "Accounts",
            },
        ),
    ]
