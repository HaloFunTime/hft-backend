from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class BingoScoreSerializer(serializers.Serializer):
    name = serializers.CharField()
    matchId = serializers.UUIDField()
    completedAt = serializers.DateTimeField()


class CheckBingoCardRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class CheckBingoCardResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    joinedChallenge = serializers.BooleanField()
    linkedGamertag = serializers.BooleanField()
    boardOrder = serializers.CharField(min_length=25, max_length=25)
    lettersCompleted = serializers.ListField(
        allow_empty=True, child=serializers.CharField(min_length=1, max_length=1)
    )
    newCompletions = serializers.ListField(
        allow_empty=True, child=BingoScoreSerializer()
    )


class CheckParticipantGamesRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class CheckParticipantGamesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalGameCount = serializers.IntegerField()
    newGameCount = serializers.IntegerField()


class JoinBingoChallengeRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class JoinBingoChallengeResponseSerializer(serializers.Serializer):
    boardOrder = serializers.CharField(min_length=25, max_length=25)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class SaveBuffRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    bingoCount = serializers.IntegerField(min_value=3)
    challengeCount = serializers.IntegerField(min_value=12)


class SaveBuffResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newBuff = serializers.BooleanField()
    blackout = serializers.BooleanField()
