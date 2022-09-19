from rest_framework import serializers


class PingResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    success = serializers.BooleanField()
