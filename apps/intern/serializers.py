from rest_framework import serializers


class InternChatterErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternChatterSerializer(serializers.Serializer):
    chatter = serializers.CharField()


class InternChatterPauseAcceptanceQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternChatterPauseAcceptanceQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternChatterPauseDenialQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternChatterPauseDenialQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternChatterPauseReverenceQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternChatterPauseReverenceQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


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


class InternNewHereWelcomeQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternNewHereWelcomeQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternNewHereYeetQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternNewHereYeetQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class InternPlusRepQuipSerializer(serializers.Serializer):
    quip = serializers.CharField()


class InternPlusRepQuipErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
