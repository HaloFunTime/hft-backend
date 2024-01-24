from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class TrailblazerScoutProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class TrailblazerScoutProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()


class TrailblazerScoutSeason3ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsSharingIsCaring = serializers.IntegerField()
    pointsBookworm = serializers.IntegerField()
    pointsOnlineWarrior = serializers.IntegerField()
    pointsHotStreak = serializers.IntegerField()
    pointsOddlyEffective = serializers.IntegerField()
    pointsTooStronk = serializers.IntegerField()


class TrailblazerScoutSeason4ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsBookworm = serializers.IntegerField()
    pointsFilmCritic = serializers.IntegerField()
    pointsOnlineWarrior = serializers.IntegerField()
    pointsTheCycle = serializers.IntegerField()
    pointsCheckeredFlag = serializers.IntegerField()
    pointsThemTharHills = serializers.IntegerField()


class TrailblazerScoutSeason5ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsOnlineWarrior = serializers.IntegerField()
    pointsHeadsOrTails = serializers.IntegerField()
    pointsHighVoltage = serializers.IntegerField()
    pointsExterminator = serializers.IntegerField()


class TrailblazerScoutEra1ProgressResponseSerializer(
    TrailblazerScoutProgressResponseSerializer
):
    pointsChurchOfTheCrab = serializers.IntegerField()
    pointsCSRGoUp = serializers.IntegerField()
    pointsPlayToSlay = serializers.IntegerField()
    pointsMeanStreets = serializers.IntegerField()
    pointsHotStreak = serializers.IntegerField()


class TrailblazerSeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class TrailblazerSeasonalRoleCheckResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    sherpa = serializers.BooleanField()
    scout = serializers.BooleanField()
