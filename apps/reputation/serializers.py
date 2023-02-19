from rest_framework import serializers


class CheckRepErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class CheckRepResponseSerializer(serializers.Serializer):
    pastYearTotalRep = serializers.IntegerField()
    pastYearUniqueRep = serializers.IntegerField()
    thisWeekRepGiven = serializers.IntegerField()
    thisWeekRepReset = serializers.CharField()


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


class TopRepErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class TopRepSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    discordId = serializers.CharField()
    pastYearTotalRep = serializers.IntegerField()
    pastYearUniqueRep = serializers.IntegerField()


class TopRepResponseSerializer(serializers.Serializer):
    topRepReceivers = TopRepSerializer(many=True, read_only=True)