from rest_framework import serializers


class CSRRequestSerializer(serializers.Serializer):
    gamertag = serializers.CharField()


class CSRDataSerializer(serializers.Serializer):
    csr = serializers.IntegerField()
    tier = serializers.CharField()
    subtier = serializers.IntegerField()


class CSRResponseSerializer(serializers.Serializer):
    gamertag = serializers.CharField()
    xuid = serializers.CharField()
    playlist_id = serializers.CharField()
    current = CSRDataSerializer()
    current_reset_max = CSRDataSerializer()
    all_time_max = CSRDataSerializer()


class SummaryMatchmakingSerializer(serializers.Serializer):
    games_played = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    ties = serializers.IntegerField()
    kills = serializers.IntegerField()
    deaths = serializers.IntegerField()
    assists = serializers.IntegerField()
    kda = serializers.FloatField()


class SummaryCustomSerializer(serializers.Serializer):
    games_played = serializers.IntegerField()


class SummaryLocalSerializer(serializers.Serializer):
    games_played = serializers.IntegerField()


class SummaryStatsResponseSerializer(serializers.Serializer):
    gamertag = serializers.CharField()
    xuid = serializers.CharField()
    matchmaking = SummaryMatchmakingSerializer()
    custom = SummaryCustomSerializer()
    local = SummaryLocalSerializer()
    games_played = serializers.IntegerField()
