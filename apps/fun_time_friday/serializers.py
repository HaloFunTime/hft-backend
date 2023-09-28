from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class PartyTimeSerializer(serializers.Serializer):
    discordId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    seconds = serializers.IntegerField()


class ReportSerializer(serializers.Serializer):
    totalPlayers = serializers.IntegerField()
    totalHours = serializers.DecimalField(max_digits=15, decimal_places=3)
    totalChannels = serializers.IntegerField()
    partyAnimals = serializers.ListField(
        allow_empty=True,
        child=PartyTimeSerializer(),
    )
    partyPoopers = serializers.ListField(
        allow_empty=True,
        child=PartyTimeSerializer(),
    )


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
