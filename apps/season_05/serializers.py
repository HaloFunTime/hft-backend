from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class JoinChallengeRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class JoinChallengeResponseSerializer(serializers.Serializer):
    assignedTeam = serializers.CharField(max_length=16)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class SaveMasterRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    domainsMastered = serializers.IntegerField(min_value=0)


class SaveMasterResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newMaster = serializers.BooleanField()
