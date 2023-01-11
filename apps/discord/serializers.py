from rest_framework import serializers

from apps.discord.models import DiscordAccount


class DiscordAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscordAccount
        fields = ["discord_id", "discord_tag"]
