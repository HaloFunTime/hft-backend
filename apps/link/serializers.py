import re

from rest_framework import serializers


class DiscordXboxLiveLinkResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField()
    discordUsername = serializers.CharField()
    xboxLiveXuid = serializers.IntegerField()
    xboxLiveGamertag = serializers.CharField()
    verified = serializers.BooleanField()


class DiscordToXboxLiveRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(max_length=20)
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    xboxLiveGamertag = serializers.CharField(min_length=1, max_length=15)

    def validate_discordUserId(self, value):
        """
        Validate that the discordUserId is numeric.
        """
        if not value.isnumeric():
            raise serializers.ValidationError("Only numeric characters are allowed.")
        return value

    def validate_xboxLiveGamertag(self, value):
        """
        Validate that the xboxLiveGamertag contains valid characters.
        """
        normalized = value.replace("#", "", 1)
        normalized_gamertag_regex = r"[ a-zA-Z][ a-zA-Z0-9]{0,14}"
        if not re.match(normalized_gamertag_regex, normalized):
            raise serializers.ValidationError(
                "Only characters constituting a valid Xbox Live Gamertag are allowed."
            )
        return normalized


class DiscordXboxLiveLinkErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
