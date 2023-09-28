from rest_framework import serializers

from apps.discord.serializers import validate_discord_id
from apps.showcase.models import ShowcaseFile


class ShowcaseFileDataSerializer(serializers.Serializer):
    isMissing = serializers.BooleanField()
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


class AddFileRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    fileType = serializers.ChoiceField(choices=ShowcaseFile.FileType)
    fileId = serializers.UUIDField()


class AddFileResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    success = serializers.BooleanField()


class RemoveFileRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    position = serializers.IntegerField()


class RemoveFileResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    success = serializers.BooleanField()
