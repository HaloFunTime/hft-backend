from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class ShowcaseFileDataSerializer(serializers.Serializer):
    fileType = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    thumbnailURL = serializers.CharField()
    waypointURL = serializers.CharField()
    plays = serializers.IntegerField()
    favorites = serializers.IntegerField()
    ratings = serializers.IntegerField()
    averageRating = serializers.DecimalField(max_digits=16, decimal_places=15)


class CheckShowcaseRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class CheckShowcaseResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    showcaseFiles = serializers.ListField(child=ShowcaseFileDataSerializer())
