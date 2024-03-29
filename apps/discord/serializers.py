from rest_framework import serializers

from apps.discord.models import DiscordAccount
from apps.overrides.serializers import validate_uuid


def validate_discord_id(value):
    """
    Validate that a Discord ID is numeric.
    """
    if not value.isnumeric():
        raise serializers.ValidationError("Only numeric characters are allowed.")
    return value


class CSRSnapshotRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )
    playlistId = serializers.CharField(required=True, validators=[validate_uuid])


class CSRSnapshot(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    currentCSR = serializers.IntegerField()
    currentResetMaxCSR = serializers.IntegerField()
    allTimeMaxCSR = serializers.IntegerField()


class CSRSnapshotResponseSerializer(serializers.Serializer):
    players = serializers.ListField(child=CSRSnapshot())


class DiscordAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordAccount
        fields = ["discord_id", "discord_username"]


class DiscordUserInfoSerializer(serializers.Serializer):
    discordId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class LFGChannelHelpPromptRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    lfgChannelId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    lfgChannelName = serializers.CharField(min_length=1, max_length=100)


class LFGChannelHelpPromptResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    new = serializers.BooleanField()


class LFGThreadHelpPromptRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    lfgThreadId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    lfgThreadName = serializers.CharField(min_length=1, max_length=100)


class LFGThreadHelpPromptResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    new = serializers.BooleanField()


class RankedRoleCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )
    playlistId = serializers.CharField(required=True, validators=[validate_uuid])


class RankedRoleCheckResponseSerializer(serializers.Serializer):
    onyx = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    diamond = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    platinum = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    gold = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    silver = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    bronze = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    unranked = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
