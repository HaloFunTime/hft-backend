from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class CheckRepErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class CheckRepResponseSerializer(serializers.Serializer):
    pastYearTotalRep = serializers.IntegerField()
    pastYearUniqueRep = serializers.IntegerField()
    thisWeekRepGiven = serializers.IntegerField()
    thisWeekRepReset = serializers.CharField()


class PartyTimerSerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    discordId = serializers.CharField()
    pastYearTotalRep = serializers.IntegerField()
    pastYearUniqueRep = serializers.IntegerField()


class PartyTimerRequestSerializer(serializers.Serializer):
    cap = serializers.IntegerField(min_value=1)
    totalRepMin = serializers.IntegerField(min_value=1)
    uniqueRepMin = serializers.IntegerField(min_value=1)
    excludeIds = serializers.CharField(required=False)

    def validate_excludeIds(self, value):
        if value is None:
            return []
        arr = value.split(",")
        arr = [validate_discord_id(x) for x in arr]
        return arr


class PartyTimerResponseSerializer(serializers.Serializer):
    partyTimers = PartyTimerSerializer(many=True, read_only=True)


class PlusRepErrorSerializer(serializers.Serializer):
    error = serializers.CharField()


class PlusRepRequestSerializer(serializers.Serializer):
    giverDiscordId = serializers.CharField()
    giverDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    receiverDiscordId = serializers.CharField()
    receiverDiscordUsername = serializers.CharField(min_length=2, max_length=32)
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
