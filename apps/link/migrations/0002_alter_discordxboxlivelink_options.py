# Generated by Django 4.1.1 on 2023-02-19 20:20

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("link", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="discordxboxlivelink",
            options={
                "ordering": ["-updated_at"],
                "verbose_name": "Discord <-> Xbox Live Link",
                "verbose_name_plural": "Discord <-> Xbox Live Links",
            },
        ),
    ]
