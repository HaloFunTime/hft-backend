from rest_framework import serializers

from apps.discord.serializers import validate_discord_id, validate_discord_tag


class HikeSubmissionPostRequestSerializer(serializers.Serializer):
    waywoPostTitle = serializers.CharField(max_length=100)
    waywoPostId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    mapSubmitterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    mapSubmitterDiscordTag = serializers.CharField(validators=[validate_discord_tag])
    scheduledPlaytestDate = serializers.DateField()
    map = serializers.CharField()
    mode1 = serializers.CharField()
    mode2 = serializers.CharField()


class HikeSubmissionPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class PathfinderDynamoProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUserTag = serializers.CharField(
        max_length=37, validators=[validate_discord_tag]
    )


class PathfinderDynamoProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()
    pointsGoneHiking = serializers.IntegerField()
    pointsMapMaker = serializers.IntegerField()
    pointsShowAndTell = serializers.IntegerField()
    pointsBookmarked = serializers.IntegerField()
    pointsPlaytime = serializers.IntegerField()
    pointsTagtacular = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderSeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUserTag = serializers.CharField(
        max_length=37, validators=[validate_discord_tag]
    )


class PathfinderSeasonalRoleCheckResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    illuminated = serializers.BooleanField()
    dynamo = serializers.BooleanField()


class WAYWOPostRequestSerializer(serializers.Serializer):
    posterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    posterDiscordTag = serializers.CharField(validators=[validate_discord_tag])
    postId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    postTitle = serializers.CharField()


class WAYWOPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
