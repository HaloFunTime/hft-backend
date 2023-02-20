import re

from rest_framework import serializers


class DiscordXboxLiveLinkResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField()
    discordUserTag = serializers.CharField()
    xboxLiveXuid = serializers.IntegerField()
    xboxLiveGamertag = serializers.CharField()
    verified = serializers.BooleanField()


class LinkDiscordToXboxLiveSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(max_length=20)
    discordUserTag = serializers.CharField(max_length=37)
    xboxLiveGamertag = serializers.CharField(min_length=1, max_length=15)

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
