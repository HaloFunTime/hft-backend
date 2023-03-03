from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class TrailblazerRoleCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class TrailblazerRoleCheckResponseSerializer(serializers.Serializer):
    sherpa = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    scout = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
