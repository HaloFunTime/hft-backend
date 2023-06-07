from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class VoiceConnectPostRequestSerializer(serializers.Serializer):
    connectorDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    connectorDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    connectedAt = serializers.DateTimeField()
    channelId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    channelName = serializers.CharField(required=False)


class VoiceConnectPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class VoiceDisconnectPostRequestSerializer(serializers.Serializer):
    disconnectorDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    disconnectorDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    disconnectedAt = serializers.DateTimeField()
    channelId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    channelName = serializers.CharField(required=False)


class VoiceDisconnectPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
