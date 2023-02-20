from rest_framework import serializers

from apps.xbox_live.models import XboxLiveAccount


class XboxLiveAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = XboxLiveAccount
        fields = ["xuid", "gamertag"]
