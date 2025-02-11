# Generated by Django 5.1.4 on 2025-02-11 07:57

import apps.era_03.models
import datetime
import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('era_03', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='boatrank',
            name='track',
            field=models.CharField(choices=[('N/A', 'N/A'), ('Command', 'Command'), ('Machinery', 'Machinery'), ('Hospitality', 'Hospitality'), ('Culinary', 'Culinary')], default='N/A', max_length=255, verbose_name='Track'),
        ),
        migrations.CreateModel(
            name='BoatAssignment',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('classification', models.CharField(choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard'), ('Command', 'Command'), ('Machinery', 'Machinery'), ('Hospitality', 'Hospitality'), ('Culinary', 'Culinary')], max_length=255, verbose_name='Classification')),
                ('description', models.TextField(blank=True, max_length=256, null=True, verbose_name='Description')),
                ('stat', models.CharField(choices=apps.era_03.models.get_stat_choices, max_length=128, verbose_name='Stat')),
                ('score', models.CharField(max_length=128, verbose_name='Score')),
                ('require_outcome', models.IntegerField(blank=True, choices=[(2, 'Win'), (3, 'Loss'), (1, 'Tie'), (4, 'Left')], null=True, verbose_name='Outcome')),
                ('require_level_id', models.UUIDField(blank=True, null=True, verbose_name='Level Canvas ID')),
                ('require_map_asset_id', models.UUIDField(blank=True, null=True, verbose_name='Map File ID')),
                ('require_mode_asset_id', models.UUIDField(blank=True, null=True, verbose_name='Mode File ID')),
                ('require_playlist_asset_id', models.UUIDField(blank=True, null=True, verbose_name='Playlist ID')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Boat Assignment',
                'verbose_name_plural': 'Boat Assignments',
                'db_table': 'BoatAssignment',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='WeeklyBoatAssignments',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('week_start', models.DateField(validators=[django.core.validators.MinValueValidator(datetime.date(2025, 2, 4)), apps.era_03.models.validate_tuesday_only], verbose_name='Week Start')),
                ('assignment_1_completion_match_id', models.UUIDField(blank=True, null=True, verbose_name='Assignment 1 Completion Match ID')),
                ('assignment_2_completion_match_id', models.UUIDField(blank=True, null=True, verbose_name='Assignment 2 Completion Match ID')),
                ('assignment_3_completion_match_id', models.UUIDField(blank=True, null=True, verbose_name='Assignment 3 Completion Match ID')),
                ('assignment_1', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='assignment_1', to='era_03.boatassignment', verbose_name='Assignment 1')),
                ('assignment_2', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='assignment_2', to='era_03.boatassignment', verbose_name='Assignment 2')),
                ('assignment_3', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, related_name='assignment_3', to='era_03.boatassignment', verbose_name='Assignment 3')),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('deckhand', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='weekly_assignments', to='era_03.boatdeckhand', verbose_name='Deckhand')),
                ('next_rank', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='next_rank', to='era_03.boatrank', verbose_name='Next Rank')),
            ],
            options={
                'verbose_name': 'Weekly Boat Assignments',
                'verbose_name_plural': 'Weekly Boat Assignments',
                'db_table': 'WeeklyBoatAssignments',
                'ordering': ['-created_at'],
            },
        ),
    ]
