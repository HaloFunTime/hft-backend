import logging

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.utils import get_current_season_id
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import (
    PathfinderHikeSubmission,
    PathfinderTestingLFGPost,
    PathfinderWAYWOPost,
)
from apps.pathfinder.serializers import (
    HikeQueueResponseSerializer,
    HikeSubmissionPostRequestSerializer,
    HikeSubmissionPostResponseSerializer,
    PathfinderDynamoProgressRequestSerializer,
    PathfinderDynamoProgressResponseSerializer,
    PathfinderDynamoSeason3ProgressResponseSerializer,
    PathfinderDynamoSeason4ProgressResponseSerializer,
    PathfinderSeasonalRoleCheckRequestSerializer,
    PathfinderSeasonalRoleCheckResponseSerializer,
    TestingLFGPostRequestSerializer,
    TestingLFGPostResponseSerializer,
    WAYWOPostRequestSerializer,
    WAYWOPostResponseSerializer,
)
from apps.pathfinder.utils import (
    get_s3_discord_earn_dict,
    get_s3_xbox_earn_dict,
    get_s4_discord_earn_dict,
    get_s4_xbox_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class HikeQueueView(APIView):
    @extend_schema(
        parameters=[],
        responses={
            200: HikeQueueResponseSerializer,
            500: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves all unplaytested PathfinderHikeSubmission records, ordered by schedule date.
        Unscheduled submissions are ordered by created date.
        """
        try:
            scheduled_incomplete_submissions = PathfinderHikeSubmission.objects.filter(
                Q(mode_1_played=False) & Q(mode_2_played=False),
                scheduled_playtest_date__isnull=False,
            ).order_by("scheduled_playtest_date", "created_at")
            scheduled = []
            for submission in scheduled_incomplete_submissions:
                scheduled.append(
                    {
                        "waywoPostId": submission.waywo_post_id,
                        "mapSubmitterDiscordId": submission.map_submitter_discord.discord_id,
                        "scheduledPlaytestDate": submission.scheduled_playtest_date,
                        "maxPlayerCount": submission.max_player_count,
                        "map": submission.map,
                        "mode1": submission.mode_1,
                        "mode2": submission.mode_2,
                    }
                )
            unscheduled_incomplete_submissions = (
                PathfinderHikeSubmission.objects.filter(
                    Q(mode_1_played=False) & Q(mode_2_played=False),
                    scheduled_playtest_date__isnull=True,
                ).order_by("created_at")
            )
            unscheduled = []
            for submission in unscheduled_incomplete_submissions:
                unscheduled.append(
                    {
                        "waywoPostId": submission.waywo_post_id,
                        "mapSubmitterDiscordId": submission.map_submitter_discord.discord_id,
                        "scheduledPlaytestDate": submission.scheduled_playtest_date,
                        "maxPlayerCount": submission.max_player_count,
                        "map": submission.map,
                        "mode1": submission.mode_1,
                        "mode2": submission.mode_2,
                    }
                )
            serializer = HikeQueueResponseSerializer(
                {
                    "scheduled": scheduled,
                    "unscheduled": unscheduled,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.error(ex)
            raise APIException(
                "Error attempting to get the queue of PathfinderHikeSubmissions."
            )


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
            map_submitter_discord_username = validation_serializer.data.get(
                "mapSubmitterDiscordUsername"
            )
            max_player_count = validation_serializer.data.get("maxPlayerCount")
            map = validation_serializer.data.get("map")
            mode_1 = validation_serializer.data.get("mode1")
            mode_2 = validation_serializer.data.get("mode2")
            try:
                map_submitter_discord = update_or_create_discord_account(
                    map_submitter_discord_id,
                    map_submitter_discord_username,
                    request.user,
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to submit a PathfinderHikeSubmission."
                )
            incomplete_hikes_for_post_id = PathfinderHikeSubmission.objects.filter(
                Q(mode_1_played=False) & Q(mode_2_played=False),
                waywo_post_id=waywo_post_id,
            )
            if len(incomplete_hikes_for_post_id) > 0:
                raise PermissionDenied(
                    "A Pathfinder Hike submission already exists for this post."
                )
            incomplete_hikes_for_submitter = PathfinderHikeSubmission.objects.filter(
                Q(mode_1_played=False) & Q(mode_2_played=False),
                map_submitter_discord_id=map_submitter_discord.discord_id,
            )
            if len(incomplete_hikes_for_submitter) > 0:
                raise PermissionDenied(
                    "A Pathfinder Hike submission has already been created by this Discord user."
                )
            try:
                PathfinderHikeSubmission.objects.create(
                    creator=request.user,
                    waywo_post_title=waywo_post_title,
                    waywo_post_id=waywo_post_id,
                    map_submitter_discord=map_submitter_discord,
                    max_player_count=max_player_count,
                    map=map,
                    mode_1=mode_1,
                    mode_2=mode_2,
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a PathfinderHikeSubmission."
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
            discord_username = validation_serializer.data.get("discordUsername")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
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


class PathfinderTestingLFGPostView(APIView):
    @extend_schema(
        request=TestingLFGPostRequestSerializer,
        responses={
            200: TestingLFGPostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Record that someone has made a Testing LFG post.
        """
        validation_serializer = TestingLFGPostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            poster_discord_id = validation_serializer.data.get("posterDiscordId")
            poster_discord_username = validation_serializer.data.get(
                "posterDiscordUsername"
            )
            post_id = validation_serializer.data.get("postId")
            post_title = validation_serializer.data.get("postTitle") or ""
            try:
                poster_discord = update_or_create_discord_account(
                    poster_discord_id, poster_discord_username, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to record a PathfinderTestingLFGPost."
                )
            try:
                PathfinderTestingLFGPost.objects.create(
                    creator=request.user,
                    poster_discord=poster_discord,
                    post_id=post_id,
                    post_title=post_title[:100],
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a PathfinderTestingLFGPost."
                )
            serializer = TestingLFGPostResponseSerializer({"success": True})
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
            poster_discord_username = validation_serializer.data.get(
                "posterDiscordUsername"
            )
            post_id = validation_serializer.data.get("postId")
            post_title = validation_serializer.data.get("postTitle") or ""
            try:
                poster_discord = update_or_create_discord_account(
                    poster_discord_id, poster_discord_username, request.user
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

        def raise_exception(ex):
            logger.error("Error attempting the Pathfinder Dynamo progress check.")
            logger.error(ex)
            raise APIException("Error attempting the Pathfinder Dynamo progress check.")

        validation_serializer = PathfinderDynamoProgressRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            try:
                season_id = get_current_season_id()
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                link = None
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    pass
            except Exception as ex:
                raise_exception(ex)

            serializer_class = None
            serializable_dict = {}
            try:
                if season_id == "3":
                    serializer_class = PathfinderDynamoSeason3ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s3_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsGoneHiking"] = discord_earns.get(
                        "gone_hiking", 0
                    )
                    serializable_dict["pointsMapMaker"] = discord_earns.get(
                        "map_maker", 0
                    )
                    serializable_dict["pointsShowAndTell"] = discord_earns.get(
                        "show_and_tell", 0
                    )

                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s3_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsBookmarked"] = xbox_earns.get(
                        "bookmarked", 0
                    )
                    serializable_dict["pointsPlaytime"] = xbox_earns.get("playtime", 0)
                    serializable_dict["pointsTagtacular"] = xbox_earns.get(
                        "tagtacular", 0
                    )
                    serializable_dict["pointsForgedInFire"] = xbox_earns.get(
                        "forged_in_fire", 0
                    )
                elif season_id == "4":
                    serializer_class = PathfinderDynamoSeason4ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s4_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsGoneHiking"] = discord_earns.get(
                        "gone_hiking", 0
                    )
                    serializable_dict["pointsTheRoadMoreTraveled"] = discord_earns.get(
                        "the_road_more_traveled", 0
                    )
                    serializable_dict["pointsBlockTalk"] = discord_earns.get(
                        "block_talk", 0
                    )
                    serializable_dict["pointsTestDriven"] = discord_earns.get(
                        "test_driven", 0
                    )

                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s4_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsShowingOff"] = xbox_earns.get(
                        "showing_off", 0
                    )
                    serializable_dict["pointsPlayOn"] = xbox_earns.get("play_on", 0)
                    serializable_dict["pointsForgedInFire"] = xbox_earns.get(
                        "forged_in_fire", 0
                    )
            except Exception as ex:
                raise_exception(ex)
            merged_dict = {
                "linkedGamertag": link is not None,
                "totalPoints": sum(serializable_dict.values()),
            } | serializable_dict
            serializer = serializer_class(merged_dict)
            return Response(serializer.data, status=status.HTTP_200_OK)
