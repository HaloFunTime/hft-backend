from .models import Identity
from rest_framework import serializers


class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = [
            "id",
            "discord_id",
            "discord_username",
            "discord_discriminator",
            "xbox_id",
            "xbox_gamertag",
        ]
