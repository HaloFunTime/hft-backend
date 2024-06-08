# Generated by Django 5.0.6 on 2024-06-05 18:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("season_05", "0008_alter_domain_medal_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="domain",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="domainchallengeteamassignment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="domainchallengeteamassignment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="domainchallengeteamreassignment",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="domainchallengeteamreassignment",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
        migrations.AlterField(
            model_name="domainmaster",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, verbose_name="Created At"),
        ),
        migrations.AlterField(
            model_name="domainmaster",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, verbose_name="Updated At"),
        ),
    ]
