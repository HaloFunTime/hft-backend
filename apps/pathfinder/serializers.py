from rest_framework import serializers

from apps.discord.serializers import DiscordUserInfoSerializer, validate_discord_id


class ChangeBeansRequestSerializer(serializers.Serializer):
    discordId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    discordUsername = serializers.CharField(min_length=2, max_length=32)
    beanDelta = serializers.IntegerField()


class ChangeBeansResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class CheckBeansRequestSerializer(DiscordUserInfoSerializer):
    pass


class CheckBeansResponseSerializer(serializers.Serializer):
    beanCount = serializers.IntegerField()


class DiscordUserAwardedBeansSerializer(serializers.Serializer):
    discordId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    awardedBeans = serializers.IntegerField()


class HikeCompletePostRequestSerializer(serializers.Serializer):
    playtestGameId = serializers.UUIDField()
    discordUsersInVoice = serializers.ListField(
        allow_empty=True, child=DiscordUserInfoSerializer()
    )
    waywoPostId = serializers.CharField(max_length=20, validators=[validate_discord_id])


class HikeCompletePostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    awardedUsers = serializers.ListField(child=DiscordUserAwardedBeansSerializer())


class HikeSubmissionSerializer(serializers.Serializer):
    waywoPostId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    mapSubmitterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    scheduledPlaytestDate = serializers.DateField(allow_null=True)
    maxPlayerCount = serializers.CharField()
    map = serializers.CharField()
    mode = serializers.CharField()


class HikeQueueResponseSerializer(serializers.Serializer):
    scheduled = HikeSubmissionSerializer(many=True, read_only=True)
    unscheduled = HikeSubmissionSerializer(many=True, read_only=True)


class HikeSubmissionPostRequestSerializer(serializers.Serializer):
    waywoPostTitle = serializers.CharField(max_length=100)
    waywoPostId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    mapSubmitterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    mapSubmitterDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    maxPlayerCount = serializers.CharField()
    map = serializers.CharField()
    mode = serializers.CharField()


class HikeSubmissionPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class PathfinderDynamoProgressRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class PathfinderDynamoProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()


class PathfinderDynamoSeason3ProgressResponseSerializer(
    PathfinderDynamoProgressResponseSerializer
):
    pointsGoneHiking = serializers.IntegerField()
    pointsMapMaker = serializers.IntegerField()
    pointsShowAndTell = serializers.IntegerField()
    pointsBookmarked = serializers.IntegerField()
    pointsPlaytime = serializers.IntegerField()
    pointsTagtacular = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderDynamoSeason4ProgressResponseSerializer(
    PathfinderDynamoProgressResponseSerializer
):
    pointsGoneHiking = serializers.IntegerField()
    pointsTheRoadMoreTraveled = serializers.IntegerField()
    pointsBlockTalk = serializers.IntegerField()
    pointsTestDriven = serializers.IntegerField()
    pointsShowingOff = serializers.IntegerField()
    pointsPlayOn = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderDynamoProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()


class PathfinderSeasonalRoleCheckRequestSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    discordUsername = serializers.CharField(min_length=2, max_length=32)


class PathfinderSeasonalRoleCheckResponseSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    illuminated = serializers.BooleanField()
    dynamo = serializers.BooleanField()


class TestingLFGPostRequestSerializer(serializers.Serializer):
    posterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    posterDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    postId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    postTitle = serializers.CharField()


class TestingLFGPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()


class WAYWOCommentRequestSerializer(serializers.Serializer):
    commenterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    commenterDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    commentId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    commentLength = serializers.IntegerField()
    postId = serializers.CharField(max_length=20, validators=[validate_discord_id])


class WAYWOCommentResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    awardedBean = serializers.BooleanField()


class WAYWOPostRequestSerializer(serializers.Serializer):
    posterDiscordId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )
    posterDiscordUsername = serializers.CharField(min_length=2, max_length=32)
    postId = serializers.CharField(max_length=20, validators=[validate_discord_id])
    postTitle = serializers.CharField()


class WAYWOPostResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
