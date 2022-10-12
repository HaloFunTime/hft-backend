from rest_framework import serializers


class InternChatterSerializer(serializers.Serializer):
    chatter = serializers.CharField()


class InternChatterPauseSerializer(serializers.Serializer):
    discord_user_id = serializers.IntegerField()
    discord_user_tag = serializers.CharField()


class InternChatterPauseResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class InternChatterErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
