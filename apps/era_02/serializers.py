from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class CheckPlayerGamesRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )


class CheckPlayerGamesResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    totalGameCount = serializers.IntegerField()
    newGameCount = serializers.IntegerField()


class CheckTeamUpChallengesRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class CheckTeamUpChallengesResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    linkedGamertag = serializers.BooleanField()
    completionsBaitTheFlags = serializers.IntegerField()
    completionsFortyFists = serializers.IntegerField()
    completionsGrenadeParade = serializers.IntegerField()
    completionsHundredHeads = serializers.IntegerField()
    completionsMostValuableDriver = serializers.IntegerField()
    completionsOwnTheZones = serializers.IntegerField()
    completionsSpeedForSeeds = serializers.IntegerField()
    completionsSpinClass = serializers.IntegerField()
    completionsStickyIcky = serializers.IntegerField()
    completionsSummonADemon = serializers.IntegerField()


class SaveMVTRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    mvtPoints = serializers.IntegerField(min_value=100)


class SaveMVTResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newMVT = serializers.BooleanField()
    maxed = serializers.BooleanField()
