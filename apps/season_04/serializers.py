from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class CheckStampsRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    funTimerRank = serializers.IntegerField(min_value=0, max_value=20)
    inviteUses = serializers.IntegerField(min_value=0)


class CheckStampsResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    stampsCompleted = serializers.IntegerField()
    scoreChatterbox = serializers.IntegerField()
    scoreFuntagious = serializers.IntegerField()
    scoreReppingIt = serializers.IntegerField()
    scoreFundurance = serializers.IntegerField()
    scoreGangsAllHere = serializers.IntegerField()
    scoreStackingDubs = serializers.IntegerField()
    scoreLicenseToKill = serializers.IntegerField()
    scoreAimForTheHead = serializers.IntegerField()
    scorePowerTrip = serializers.IntegerField()
    scoreBotBullying = serializers.IntegerField()
    scoreOneFundo = serializers.IntegerField()
    scoreGleeFiddy = serializers.IntegerField()
    scoreWellTraveled = serializers.IntegerField()
    scoreMoModesMoFun = serializers.IntegerField()
    scorePackedHouse = serializers.IntegerField()
    completedFinishInFive = serializers.BooleanField()
    completedVictoryLap = serializers.BooleanField()
    completedTypeA = serializers.BooleanField()
    completedFormerlyChucks = serializers.BooleanField()
    completedInParticular = serializers.BooleanField()
