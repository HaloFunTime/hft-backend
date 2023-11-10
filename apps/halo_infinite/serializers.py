from rest_framework import serializers


class CareerRankResponseSerializer(serializers.Serializer):
    gamertag = serializers.CharField()
    xuid = serializers.CharField()
    currentRankNumber = serializers.IntegerField()
    currentRankName = serializers.CharField()
    currentRankScore = serializers.IntegerField()
    currentRankScoreMax = serializers.IntegerField()
    cumulativeScore = serializers.IntegerField()
    cumulativeScoreMax = serializers.IntegerField()


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


class VariantSerializer(serializers.Serializer):
    AssetKind = serializers.IntegerField()
    AssetId = serializers.UUIDField()
    VersionId = serializers.UUIDField()


class MatchInfoSerializer(serializers.Serializer):
    StartTime = serializers.CharField()
    EndTime = serializers.CharField()
    Duration = serializers.CharField()
    LifecycleMode = serializers.IntegerField()
    GameVariantCategory = serializers.IntegerField()
    LevelId = serializers.UUIDField()
    MapVariant = VariantSerializer()
    UgcGameVariant = VariantSerializer()
    ClearanceId = serializers.UUIDField()
    Playlist = VariantSerializer()
    PlaylistExperience = serializers.IntegerField()
    PlaylistMapModePair = VariantSerializer()
    SeasonId = serializers.CharField()
    PlayableDuration = serializers.CharField()
    TeamsEnabled = serializers.BooleanField()
    TeamScoringEnabled = serializers.BooleanField()
    GameplayInteraction = serializers.IntegerField()


class RecentGameSerializer(serializers.Serializer):
    matchId = serializers.CharField()
    outcome = serializers.CharField()
    finished = serializers.BooleanField()
    modeName = serializers.CharField()
    modeAssetId = serializers.CharField()
    modeVersionId = serializers.CharField()
    mapName = serializers.CharField()
    mapAssetId = serializers.CharField()
    mapVersionId = serializers.CharField()
    playlistName = serializers.CharField()
    playlistAssetId = serializers.CharField()
    playlistVersionId = serializers.CharField()


class RecentGamesResponseSerializer(serializers.Serializer):
    games = RecentGameSerializer(many=True)


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
