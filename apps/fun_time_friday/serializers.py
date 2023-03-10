from rest_framework import serializers

from apps.discord.serializers import validate_discord_id, validate_discord_tag


class VoiceConnectPostRequestSerializer(serializers.Serializer):
    connectorDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    connectorDiscordTag = serializers.CharField(validators=[validate_discord_tag])
    connectedAt = serializers.DateTimeField()
    channelId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    channelName = serializers.CharField(required=False)


class VoiceConnectPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class VoiceDisconnectPostRequestSerializer(serializers.Serializer):
    disconnectorDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    disconnectorDiscordTag = serializers.CharField(validators=[validate_discord_tag])
    disconnectedAt = serializers.DateTimeField()
    channelId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    channelName = serializers.CharField(required=False)


class VoiceDisconnectPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
