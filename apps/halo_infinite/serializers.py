from rest_framework import serializers


class CSRRequestSerializer(serializers.Serializer):
    gamertag = serializers.CharField()


class CSRDataSerializer(serializers.Serializer):
    csr = serializers.IntegerField()
    tier = serializers.CharField()
    subtier = serializers.IntegerField()
    tierDescription = serializers.CharField()


class CSRPlaylistSerializer(serializers.Serializer):
    playlistId = serializers.CharField()
    playlistName = serializers.CharField()
    playlistDescription = serializers.CharField()
    current = CSRDataSerializer()
    currentResetMax = CSRDataSerializer()
    allTimeMax = CSRDataSerializer()


class CSRResponseSerializer(serializers.Serializer):
    gamertag = serializers.CharField()
    xuid = serializers.CharField()
    playlists = CSRPlaylistSerializer(many=True)


class SummaryMatchmakingSerializer(serializers.Serializer):
    gamesPlayed = serializers.IntegerField()
    wins = serializers.IntegerField()
    losses = serializers.IntegerField()
    ties = serializers.IntegerField()
    kills = serializers.IntegerField()
    deaths = serializers.IntegerField()
    assists = serializers.IntegerField()
    kda = serializers.FloatField()


class SummaryCustomSerializer(serializers.Serializer):
    gamesPlayed = serializers.IntegerField()


class SummaryLocalSerializer(serializers.Serializer):
    gamesPlayed = serializers.IntegerField()


class SummaryStatsResponseSerializer(serializers.Serializer):
    gamertag = serializers.CharField()
    xuid = serializers.CharField()
    matchmaking = SummaryMatchmakingSerializer()
    custom = SummaryCustomSerializer()
    local = SummaryLocalSerializer()
    gamesPlayed = serializers.IntegerField()
