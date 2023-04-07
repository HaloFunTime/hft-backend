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
    PathfinderDynamoProgressRequestSerializer,
    PathfinderDynamoProgressResponseSerializer,
    PathfinderSeasonalRoleCheckRequestSerializer,
    PathfinderSeasonalRoleCheckResponseSerializer,
    WAYWOPostRequestSerializer,
    WAYWOPostResponseSerializer,
)
from apps.pathfinder.utils import (
    get_s3_discord_earn_dict,
    get_s3_xbox_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
)
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
        Evaluate a Discord User ID by retrieving its verified linked Xbox Live gamertag, querying stats from the Halo
        Infinite API and the HFT DB, and returning a payload indicating the seasonal Pathfinder progression roles the
        Discord User ID qualifies for, if any.
        """
        validation_serializer = PathfinderSeasonalRoleCheckRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_tag = validation_serializer.data.get("discordUserTag")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_tag, request.user
                )
                link = None
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    pass

                illuminated_qualified = False
                dynamo_qualified = False
                if link is not None:
                    illuminated_qualified = is_illuminated_qualified(
                        link.xbox_live_account_id
                    )
                    dynamo_qualified = is_dynamo_qualified(
                        discord_account.discord_id, link.xbox_live_account_id
                    )
                else:
                    dynamo_qualified = is_dynamo_qualified(
                        discord_account.discord_id, None
                    )
            except Exception as ex:
                logger.error("Error attempting the Pathfinder seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Pathfinder seasonal role check."
                )
            serializer = PathfinderSeasonalRoleCheckResponseSerializer(
                {
                    "discordUserId": discord_account.discord_id,
                    "illuminated": illuminated_qualified,
                    "dynamo": dynamo_qualified,
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


class PathfinderDynamoProgressView(APIView):
    @extend_schema(
        request=PathfinderDynamoProgressRequestSerializer,
        responses={
            200: PathfinderDynamoProgressResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate an individual Discord ID's progress toward the Pathfinder Dynamo role.
        """
        validation_serializer = PathfinderDynamoProgressRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_tag = validation_serializer.data.get("discordUserTag")
            points_gone_hiking = 0
            points_map_maker = 0
            points_show_and_tell = 0
            points_bookmarked = 0
            points_playtime = 0
            points_tagtacular = 0
            points_forged_in_fire = 0
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_tag, request.user
                )

                # Tally the Discord Points
                discord_earns = get_s3_discord_earn_dict(
                    [discord_account.discord_id]
                ).get(discord_account.discord_id)
                points_gone_hiking = discord_earns.get("gone_hiking")
                points_map_maker = discord_earns.get("map_maker")
                points_show_and_tell = discord_earns.get("show_and_tell")

                # Tally the Xbox Points
                link = None
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                    xbox_earns = get_s3_xbox_earn_dict([link.xbox_live_account_id]).get(
                        link.xbox_live_account_id
                    )
                    points_bookmarked = xbox_earns.get("bookmarked")
                    points_playtime = xbox_earns.get("playtime")
                    points_tagtacular = xbox_earns.get("tagtacular")
                    points_forged_in_fire = xbox_earns.get("forged_in_fire")
                except DiscordXboxLiveLink.DoesNotExist:
                    pass

                # Calculate the total points
                total_points = (
                    points_gone_hiking
                    + points_map_maker
                    + points_show_and_tell
                    + points_bookmarked
                    + points_playtime
                    + points_tagtacular
                    + points_forged_in_fire
                )
            except Exception as ex:
                logger.error("Error attempting the Pathfinder Dynamo progress check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Pathfinder Dynamo progress check."
                )
            serializer = PathfinderDynamoProgressResponseSerializer(
                {
                    "linkedGamertag": link is not None,
                    "totalPoints": total_points,
                    "pointsGoneHiking": points_gone_hiking,
                    "pointsMapMaker": points_map_maker,
                    "pointsShowAndTell": points_show_and_tell,
                    "pointsBookmarked": points_bookmarked,
                    "pointsPlaytime": points_playtime,
                    "pointsTagtacular": points_tagtacular,
                    "pointsForgedInFire": points_forged_in_fire,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
