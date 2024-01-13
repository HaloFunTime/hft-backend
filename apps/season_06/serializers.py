from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class JoinChallengeRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class JoinChallengeResponseSerializer(serializers.Serializer):
    boardOrder = serializers.CharField(min_length=25, max_length=25)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class SaveBuffRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    bingoCount = serializers.IntegerField(min_value=3)
    challengeCount = serializers.IntegerField(min_value=12)


class SaveBuffResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newBuff = serializers.BooleanField()
    blackout = serializers.BooleanField()
