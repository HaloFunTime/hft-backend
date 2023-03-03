from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class PathfinderRoleCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class PathfinderRoleCheckResponseSerializer(serializers.Serializer):
    illuminated = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    dynamo = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
