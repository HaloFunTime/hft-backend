from rest_framework import serializers

from apps.discord.serializers import (
    DiscordUserInfoSerializer,
    validate_discord_id,
    validate_uuid,
)


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


class DiscordUserAwardedBeansSerializer(DiscordUserInfoSerializer):
    awardedBeans = serializers.IntegerField()


class HikeCompletePostRequestSerializer(serializers.Serializer):
    playtestGameId = serializers.UUIDField()
    discordUsersInVoice = serializers.ListField(
        allow_empty=True, child=DiscordUserInfoSerializer()
    )
    waywoPostTitle = serializers.CharField(max_length=100)
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


class PathfinderDynamoEra1ProgressResponseSerializer(
    PathfinderDynamoProgressResponseSerializer
):
    pointsGoneHiking = serializers.IntegerField()
    pointsBeanSpender = serializers.IntegerField()
    pointsWhatAreYouWorkingOn = serializers.IntegerField()
    pointsFeedbackFiend = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderDynamoEra2ProgressResponseSerializer(
    PathfinderDynamoProgressResponseSerializer
):
    pointsGoneHiking = serializers.IntegerField()
    pointsBeanSpender = serializers.IntegerField()
    pointsWhatAreYouWorkingOn = serializers.IntegerField()
    pointsFeedbackFiend = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderDynamoEra3ProgressResponseSerializer(
    PathfinderDynamoProgressResponseSerializer
):
    pointsWhatAreYouWorkingOn = serializers.IntegerField()
    pointsFeedbackFiend = serializers.IntegerField()
    pointsForgedInFire = serializers.IntegerField()


class PathfinderDynamoProgressResponseSerializer(serializers.Serializer):
    linkedGamertag = serializers.BooleanField()
    totalPoints = serializers.IntegerField()


class PathfinderProdigyCheckSerializer(serializers.Serializer):
    discordUserId = serializers.CharField(
        max_length=20, validators=[validate_discord_id]
    )


class PathfinderProdigyCheckRequestSerializer(serializers.Serializer):
    discordUserIds = serializers.ListField(
        allow_empty=True,
        child=serializers.CharField(max_length=20, validators=[validate_discord_id]),
    )


class PathfinderProdigyCheckResponseSerializer(serializers.Serializer):
    yes = serializers.ListField(
        allow_empty=True, child=PathfinderProdigyCheckSerializer()
    )
    no = serializers.ListField(
        allow_empty=True, child=PathfinderProdigyCheckSerializer()
    )


class PopularFileSerializer(serializers.Serializer):
    assetId = serializers.CharField(required=True, validators=[validate_uuid])
    versionId = serializers.CharField(required=True, validators=[validate_uuid])
    fileType = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    description = serializers.CharField()
    playsRecent = serializers.IntegerField()
    playsAllTime = serializers.IntegerField()
    thumbnailUrl = serializers.CharField(required=True)
    waypointUrl = serializers.CharField()
    bookmarks = serializers.IntegerField()
    contributorDiscordIds = serializers.ListField(
        child=serializers.CharField(max_length=20, validators=[validate_discord_id])
    )
    tags = serializers.ListField(child=serializers.CharField())
    averageRating = serializers.DecimalField(max_digits=16, decimal_places=15)
    numberOfRatings = serializers.IntegerField()


class PopularFilesResponseSerializer(serializers.Serializer):
    files = PopularFileSerializer(many=True, read_only=True)


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


class WeeklyRecapRequestSerializer(serializers.Serializer):
    discordUsersAwardedBeans = serializers.ListField(
        allow_empty=True, child=DiscordUserAwardedBeansSerializer()
    )


class WeeklyRecapResponseSerializer(serializers.Serializer):
    hikerCount = serializers.IntegerField()
    hikeSubmissionCount = serializers.IntegerField()
    waywoCommentCount = serializers.IntegerField()
    waywoPostCount = serializers.IntegerField()
