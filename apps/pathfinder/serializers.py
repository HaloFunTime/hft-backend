from rest_framework import serializers

from apps.discord.serializers import validate_discord_id, validate_discord_tag


class HikeSubmissionPostRequestSerializer(serializers.Serializer):
    waywoPostTitle = serializers.CharField(max_length=100)
    waywoPostId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    mapSubmitterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    mapSubmitterDiscordTag = serializers.CharField(validators=[validate_discord_tag])
    scheduledPlaytestDate = serializers.DateField()
    map = serializers.CharField()
    mode1 = serializers.CharField()
    mode2 = serializers.CharField()


class HikeSubmissionPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class SeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class SeasonalRoleCheckResponseSerializer(serializers.Serializer):
    illuminated = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    dynamo = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
