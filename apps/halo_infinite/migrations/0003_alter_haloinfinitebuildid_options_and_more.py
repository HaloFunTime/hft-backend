# Generated by Django 4.1.1 on 2023-03-05 22:29

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("halo_infinite", "0002_haloinfiniteseason_haloinfiniteplaylist"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="haloinfinitebuildid",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Build ID",
                "verbose_name_plural": "Build IDs",
            },
        ),
        migrations.AlterModelOptions(
            name="haloinfiniteclearancetoken",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Clearance Token",
                "verbose_name_plural": "Clearance Tokens",
            },
        ),
        migrations.AlterModelOptions(
            name="haloinfiniteplaylist",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Playlist",
                "verbose_name_plural": "Playlists",
            },
        ),
        migrations.AlterModelOptions(
            name="haloinfiniteseason",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Season",
                "verbose_name_plural": "Seasons",
            },
        ),
        migrations.AlterModelOptions(
            name="haloinfinitespartantoken",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Spartan Token",
                "verbose_name_plural": "Spartan Tokens",
            },
        ),
        migrations.AlterModelOptions(
            name="haloinfinitexststoken",
            options={
                "ordering": ["-created_at"],
                "verbose_name": "XSTS Token",
                "verbose_name_plural": "XSTS Tokens",
            },
        ),
    ]
