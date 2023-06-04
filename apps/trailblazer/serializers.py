from rest_framework import serializers

from apps.discord.serializers import validate_discord_id, validate_discord_tag


class TrailblazerScoutProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUserTag = serializers.CharField(
        max_length=37, validators=[validate_discord_tag]
    )


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


class TrailblazerSeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUserTag = serializers.CharField(
        max_length=37, validators=[validate_discord_tag]
    )


class TrailblazerSeasonalRoleCheckResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    sherpa = serializers.BooleanField()
    scout = serializers.BooleanField()
