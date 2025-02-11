from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class BoardBoatRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class BoardBoatResponseSerializer(serializers.Serializer):
    rank = serializers.CharField(max_length=255)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class CheckBoatAssignmentsRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class CheckBoatAssignmentsResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    joinedChallenge = serializers.BooleanField()
    linkedGamertag = serializers.BooleanField()
    currentRank = serializers.CharField(max_length=255)
    currentRankTier = serializers.IntegerField(min_value=1)
    assignment1 = serializers.CharField(max_length=255)
    assignment1Completed = serializers.BooleanField()
    assignment2 = serializers.CharField(max_length=255)
    assignment2Completed = serializers.BooleanField()
    assignment3 = serializers.CharField(max_length=255)
    assignment3Completed = serializers.BooleanField()
    assignmentsCompleted = serializers.BooleanField()
    existingAssignments = serializers.BooleanField()
    justPromoted = serializers.BooleanField()


class CheckDeckhandGamesRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class CheckDeckhandGamesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalGameCount = serializers.IntegerField()
    newGameCount = serializers.IntegerField()


class SaveBoatCaptainRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    rankTier = serializers.IntegerField(min_value=1)


class SaveBoatCaptainResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newBoatCaptain = serializers.BooleanField()
