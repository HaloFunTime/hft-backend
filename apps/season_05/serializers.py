from rest_framework import serializers

from apps.discord.serializers import validate_discord_id


class DomainScoreSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField()
    effectiveDate = serializers.DateField()
    currentScore = serializers.IntegerField()
    maxScore = serializers.IntegerField()
    isMastered = serializers.BooleanField()


class CheckDomainsRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class CheckDomainsResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    joinedChallenge = serializers.BooleanField()
    linkedGamertag = serializers.BooleanField()
    assignedTeam = serializers.CharField(max_length=16)
    domainsMastered = serializers.IntegerField()
    domainScores = serializers.ListField(child=DomainScoreSerializer())


class DomainTeamScoreSerializer(serializers.Serializer):
    team = serializers.CharField()
    memberCount = serializers.IntegerField()
    domainsMastered = serializers.IntegerField()


class CheckTeamsResponseSerializer(serializers.Serializer):
    teamScores = serializers.ListField(child=DomainTeamScoreSerializer())


class JoinChallengeRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class JoinChallengeResponseSerializer(serializers.Serializer):
    assignedTeam = serializers.CharField(max_length=16)
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newJoiner = serializers.BooleanField()


class ProcessedReassignmentSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    team = serializers.CharField()
    reason = serializers.CharField()


class ProcessReassignmentsRequestSerializer(serializers.Serializer):
    date = serializers.DateField()


class ProcessReassignmentsResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    processedReassignments = serializers.ListField(
        child=ProcessedReassignmentSerializer()
    )


class SaveMasterRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    domainsMastered = serializers.IntegerField(min_value=0)


class SaveMasterResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    newMaster = serializers.BooleanField()
