from rest_framework import serializers

from apps.discord.serializers import validate_discord_id
from apps.overrides.serializers import validate_uuid


class TrailblazerScoutProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class TrailblazerScoutProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()


class TrailblazerScoutEra1ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsCSRGoUp = serializers.IntegerField()
    pointsPlayToSlay = serializers.IntegerField()
    pointsMeanStreets = serializers.IntegerField()
    pointsHotStreak = serializers.IntegerField()


class TrailblazerScoutEra2ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsCSRGoUp = serializers.IntegerField()
    pointsTooStronk = serializers.IntegerField()
    pointsScoreboard = serializers.IntegerField()
    pointsTheCycle = serializers.IntegerField()


class TrailblazerScoutEra3ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsCSRGoUp = serializers.IntegerField()
    pointsBombDotCom = serializers.IntegerField()
    pointsOddlyEffective = serializers.IntegerField()
    pointsItsTheAge = serializers.IntegerField()
    pointsOverkill = serializers.IntegerField()


class TrailblazerTitanCheckSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    currentCSR = serializers.IntegerField()


class TrailblazerTitanCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )
    playlistId = serializers.CharField(required=True, validators=[validate_uuid])


class TrailblazerTitanCheckResponseSerializer(serializers.Serializer):
    yes = serializers.ListField(
        allow_empty=True, child=TrailblazerTitanCheckSerializer()
    )
    no = serializers.ListField(
        allow_empty=True, child=TrailblazerTitanCheckSerializer()
    )
    thresholdCSR = serializers.IntegerField()
