from rest_framework import serializers


class InternChatterErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternChatterSerializer(serializers.Serializer):
    chatter = serializers.CharField()


class InternChatterPauseErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternChatterPauseRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField()
    discordUserTag = serializers.CharField()


class InternChatterPauseResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class InternHelpfulHintSerializer(serializers.Serializer):
    hint = serializers.CharField()


class InternHelpfulHintErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
