from rest_framework import serializers

from apps.discord.serializers import validate_discord_id, validate_discord_tag


class TrailblazerScoutProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUserTag = serializers.CharField(
        max_length=37, validators=[validate_discord_tag]
    )


class TrailblazerScoutProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsSharingIsCaring = serializers.IntegerField()
    pointsBookworm = serializers.IntegerField()
    pointsOnlineWarrior = serializers.IntegerField()
    pointsHotStreak = serializers.IntegerField()
    pointsOddlyEffective = serializers.IntegerField()
    pointsTooStronk = serializers.IntegerField()


class TrailblazerSeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class TrailblazerSeasonalRoleCheckResponseSerializer(serializers.Serializer):
    sherpa = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    scout = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
