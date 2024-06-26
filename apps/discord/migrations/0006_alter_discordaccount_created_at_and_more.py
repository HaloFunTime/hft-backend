# Generated by Django 5.0.6 on 2024-06-05 18:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("discord", "0005_discordlfgchannelhelpprompt"),
    ]

    operations = [
        migrations.AlterField(
            model_name="discordaccount",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="discordaccount",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="discordlfgchannelhelpprompt",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="discordlfgchannelhelpprompt",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="discordlfgthreadhelpprompt",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="discordlfgthreadhelpprompt",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
    ]
