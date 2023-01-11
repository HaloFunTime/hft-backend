from rest_framework import serializers


class PlusRepErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class PlusRepRequestSerializer(serializers.Serializer):
    giverDiscordId = serializers.CharField()
    giverDiscordTag = serializers.CharField()
    receiverDiscordId = serializers.CharField()
    receiverDiscordTag = serializers.CharField()
    message = serializers.CharField()


class PlusRepResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
