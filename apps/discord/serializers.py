import re

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


def validate_discord_tag(value):
    """
    Validate that a Discord Tag has a username, # character, and a four-digit numeric discriminator.
    """
    discord_tag_regex = r".+\d{4}$"
    if not re.match(discord_tag_regex, value):
        raise serializers.ValidationError(
            "Only characters constituting a valid Discord Tag are allowed."
        )
    return value


class DiscordAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordAccount
        fields = ["discord_id", "discord_tag"]


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
