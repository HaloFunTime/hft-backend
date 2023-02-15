import re

from rest_framework import serializers

from apps.discord.serializers import DiscordAccountSerializer
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.serializers import XboxLiveAccountSerializer


class DiscordXboxLiveLinkSerializer(serializers.ModelSerializer):
    discord_account = DiscordAccountSerializer(read_only=True)
    xbox_live_account = XboxLiveAccountSerializer(read_only=True)

    class Meta:
        model = DiscordXboxLiveLink
        fields = ["discord_account", "xbox_live_account", "verified"]


class LinkDiscordAndXboxLiveSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(max_length=20)
    discordUserTag = serializers.CharField(max_length=37)
    xboxLiveGamertag = serializers.CharField(min_length=3, max_length=15)

    def validate_discordUserId(self, value):
        """
        Validate that the discordUserId is numeric.
        """
        if not value.isnumeric():
            raise serializers.ValidationError("Only numeric characters are allowed.")
        return value

    def validate_discordUserTag(self, value):
        """
        Validate that the discordUserTag is properly formatted.
        """
        if value.count("#") != 1:
            raise serializers.ValidationError("One '#' character is required.")
        return value

    def validate_xboxLiveGamertag(self, value):
        """
        Validate that the xboxLiveGamertag contains valid characters.
        """
        squished = value.replace(" ", "").replace("#", "", 1)
        squished_gamertag_regex = r"[a-zA-Z][a-zA-Z0-9]{0,14}"
        if not re.match(squished_gamertag_regex, squished):
            raise serializers.ValidationError(
                "Only characters constituting a valid Xbox Live Gamertag are allowed."
            )
        return value


class LinkDiscordAndXboxLiveErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
