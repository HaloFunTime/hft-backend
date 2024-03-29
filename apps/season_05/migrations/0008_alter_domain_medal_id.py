# Generated by Django 4.1.1 on 2023-10-31 16:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("season_05", "0007_alter_domain_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="domain",
            name="medal_id",
            field=models.DecimalField(
                blank=True,
                decimal_places=0,
                max_digits=15,
                null=True,
                verbose_name="Medal ID (only necessary if Stat is 'Medal Count')",
            ),
        ),
    ]
