import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import PathfinderHikeSubmission, PathfinderWAYWOPost
from apps.pathfinder.serializers import (
    HikeSubmissionPostRequestSerializer,
    HikeSubmissionPostResponseSerializer,
    PathfinderSeasonalRoleCheckRequestSerializer,
    PathfinderSeasonalRoleCheckResponseSerializer,
    WAYWOPostRequestSerializer,
    WAYWOPostResponseSerializer,
)
from apps.pathfinder.utils import get_dynamo_qualified, get_illuminated_qualified
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class HikeSubmissionView(APIView):
    @extend_schema(
        request=HikeSubmissionPostRequestSerializer,
        responses={
            200: HikeSubmissionPostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Submit a map for playtesting consideration (if eligible) and record relevant info about the submitter.
        """
        validation_serializer = HikeSubmissionPostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            waywo_post_title = validation_serializer.data.get("waywoPostTitle")
            waywo_post_id = validation_serializer.data.get("waywoPostId")
            map_submitter_discord_id = validation_serializer.data.get(
                "mapSubmitterDiscordId"
            )
            map_submitter_discord_tag = validation_serializer.data.get(
                "mapSubmitterDiscordTag"
            )
            scheduled_playtest_date = validation_serializer.data.get(
                "scheduledPlaytestDate"
            )
            map = validation_serializer.data.get("map")
            mode_1 = validation_serializer.data.get("mode1")
            mode_2 = validation_serializer.data.get("mode2")
            try:
                map_submitter_discord = update_or_create_discord_account(
                    map_submitter_discord_id, map_submitter_discord_tag, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to submit a PathfinderHikeSubmission."
                )
            hikes_for_post_id = PathfinderHikeSubmission.objects.filter(
                scheduled_playtest_date=scheduled_playtest_date,
                waywo_post_id=waywo_post_id,
            )
            if len(hikes_for_post_id) > 0:
                raise PermissionDenied(
                    "A Pathfinder Hike submission already exists for this post."
                )
            hikes_for_submitter = PathfinderHikeSubmission.objects.filter(
                scheduled_playtest_date=scheduled_playtest_date,
                map_submitter_discord_id=map_submitter_discord.discord_id,
            )
            if len(hikes_for_submitter) > 0:
                raise PermissionDenied(
                    "A Pathfinder Hike submission has already been created by this Discord user."
                )
            try:
                PathfinderHikeSubmission.objects.create(
                    creator=request.user,
                    waywo_post_title=waywo_post_title,
                    waywo_post_id=waywo_post_id,
                    map_submitter_discord=map_submitter_discord,
                    scheduled_playtest_date=scheduled_playtest_date,
                    map=map,
                    mode_1=mode_1,
                    mode_2=mode_2,
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to submit a PathfinderHikeSubmission."
                )
            serializer = HikeSubmissionPostResponseSerializer({"success": True})
            return Response(serializer.data, status=status.HTTP_200_OK)


class PathfinderSeasonalRoleCheckView(APIView):
    @extend_schema(
        request=PathfinderSeasonalRoleCheckRequestSerializer,
        responses={
            200: PathfinderSeasonalRoleCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API and the HFT DB, and returning a payload indicating the seasonal Pathfinder progression role
        each Discord ID qualifies for, if any.
        """
        validation_serializer = PathfinderSeasonalRoleCheckRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            try:
                # Get all verified DiscordXboxLiveLink records matching the input discordUserIDs
                links = list(
                    DiscordXboxLiveLink.objects.filter(
                        discord_account_id__in=discord_ids
                    )
                    .filter(verified=True)
                    .order_by("created_at")
                )

                # Retrieve qualifying Sherpa/Scout IDs from the utility methods
                illuminated_discord_ids = get_illuminated_qualified(links)
                dynamo_discord_ids = get_dynamo_qualified(links)
            except Exception as ex:
                logger.error("Error attempting the Pathfinder seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Pathfinder seasonal role check."
                )
            serializer = PathfinderSeasonalRoleCheckResponseSerializer(
                {
                    "illuminated": illuminated_discord_ids,
                    "dynamo": dynamo_discord_ids,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class PathfinderWAYWOPostView(APIView):
    @extend_schema(
        request=WAYWOPostRequestSerializer,
        responses={
            200: WAYWOPostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Record that someone has made a WAYWO post.
        """
        validation_serializer = WAYWOPostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            poster_discord_id = validation_serializer.data.get("posterDiscordId")
            poster_discord_tag = validation_serializer.data.get("posterDiscordTag")
            post_id = validation_serializer.data.get("postId")
            post_title = validation_serializer.data.get("postTitle") or ""
            try:
                poster_discord = update_or_create_discord_account(
                    poster_discord_id, poster_discord_tag, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException("Error attempting to record a PathfinderWAYWOPost.")
            try:
                PathfinderWAYWOPost.objects.create(
                    creator=request.user,
                    poster_discord=poster_discord,
                    post_id=post_id,
                    post_title=post_title[:100],
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException("Error attempting to create a PathfinderWAYWOPost.")
            serializer = WAYWOPostResponseSerializer({"success": True})
            return Response(serializer.data, status=status.HTTP_200_OK)
