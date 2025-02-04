from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class BoardBoatRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class BoardBoatResponseSerializer(serializers.Serializer):
    rank = serializers.CharField(max_length=255)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class CheckDeckhandGamesRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class CheckDeckhandGamesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalGameCount = serializers.IntegerField()
    newGameCount = serializers.IntegerField()


class SaveBoatCaptainRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    rankTier = serializers.IntegerField(min_value=1)


class SaveBoatCaptainResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newBoatCaptain = serializers.BooleanField()
