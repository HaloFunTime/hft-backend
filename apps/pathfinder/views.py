import datetime
import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.models import DiscordAccount
from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.api.search import search_halofuntime_popular
from apps.halo_infinite.constants import SEARCH_ASSET_KINDS
from apps.halo_infinite.exceptions import (
    MissingEraDataException,
    MissingSeasonDataException,
)
from apps.halo_infinite.utils import (
    get_contributor_xuids_for_maps_in_active_playlists,
    get_current_era,
    get_current_season_id,
    get_waypoint_file_url,
    update_known_playlists,
)
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import (
    PathfinderHikeGameParticipation,
    PathfinderHikeSubmission,
    PathfinderHikeVoiceParticipation,
    PathfinderTestingLFGPost,
    PathfinderWAYWOComment,
    PathfinderWAYWOPost,
)
from apps.pathfinder.serializers import (
    ChangeBeansRequestSerializer,
    ChangeBeansResponseSerializer,
    CheckBeansRequestSerializer,
    CheckBeansResponseSerializer,
    DiscordUserAwardedBeansSerializer,
    HikeCompletePostRequestSerializer,
    HikeCompletePostResponseSerializer,
    HikeQueueResponseSerializer,
    HikeSubmissionPostRequestSerializer,
    HikeSubmissionPostResponseSerializer,
    PathfinderDynamoEra1ProgressResponseSerializer,
    PathfinderDynamoProgressRequestSerializer,
    PathfinderDynamoProgressResponseSerializer,
    PathfinderDynamoSeason3ProgressResponseSerializer,
    PathfinderDynamoSeason4ProgressResponseSerializer,
    PathfinderDynamoSeason5ProgressResponseSerializer,
    PathfinderProdigyCheckRequestSerializer,
    PathfinderProdigyCheckResponseSerializer,
    PathfinderProdigyCheckSerializer,
    PathfinderSeasonalRoleCheckRequestSerializer,
    PathfinderSeasonalRoleCheckResponseSerializer,
    PopularFileSerializer,
    PopularFilesResponseSerializer,
    TestingLFGPostRequestSerializer,
    TestingLFGPostResponseSerializer,
    WAYWOCommentRequestSerializer,
    WAYWOCommentResponseSerializer,
    WAYWOPostRequestSerializer,
    WAYWOPostResponseSerializer,
    WeeklyRecapRequestSerializer,
    WeeklyRecapResponseSerializer,
)
from apps.pathfinder.utils import (
    BEAN_AWARD_HIKE_GAME_PARTICIPATION,
    BEAN_AWARD_HIKE_VOICE_PARTICIPATION,
    BEAN_AWARD_WAYWO_COMMENT,
    BEAN_COST_HIKE_SUBMISSION,
    PATHFINDER_WAYWO_COMMENT_MIN_LENGTH_FOR_BEAN_AWARD,
    change_beans,
    check_beans,
    get_e1_discord_earn_dict,
    get_e1_xbox_earn_dict,
    get_s3_discord_earn_dict,
    get_s3_xbox_earn_dict,
    get_s4_discord_earn_dict,
    get_s4_xbox_earn_dict,
    get_s5_discord_earn_dict,
    get_s5_xbox_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


def now_utc():
    return datetime.datetime.now(tz=datetime.timezone.utc)


class ChangeBeansView(APIView):
    @extend_schema(
        request=ChangeBeansRequestSerializer,
        responses={
            200: ChangeBeansResponseSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Changes the Pathfinder Bean Count for a given Discord user by 'beanDelta'.
        """
        validation_serializer = ChangeBeansRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordId")
            discord_username = validation_serializer.data.get("discordUsername")
            bean_delta = validation_serializer.data.get("beanDelta")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                success = change_beans(discord_account, bean_delta)
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to change a Pathfinder Bean Count."
                )
            serializer = ChangeBeansResponseSerializer({"success": success})
            return Response(serializer.data, status=status.HTTP_200_OK)


class CheckBeansView(APIView):
    @extend_schema(
        request=CheckBeansRequestSerializer,
        responses={
            200: CheckBeansResponseSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Returns the Pathfinder Bean Count for a given Discord user.
        """
        validation_serializer = CheckBeansRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordId")
            discord_username = validation_serializer.data.get("discordUsername")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                bean_count = check_beans(discord_account)
            except Exception as ex:
                logger.error(ex)
                raise APIException("Error attempting to check a Pathfinder Bean Count.")
            serializer = CheckBeansResponseSerializer({"beanCount": bean_count})
            return Response(serializer.data, status=status.HTTP_200_OK)


class HikeCompleteView(APIView):
    @extend_schema(
        request=HikeCompletePostRequestSerializer,
        responses={
            200: HikeCompletePostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Mark a Pathfinder Hike complete and save/update relevant additional records.
        """
        validation_serializer = HikeCompletePostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            playtest_game_id = validation_serializer.data.get("playtestGameId")
            discord_users_in_voice = validation_serializer.data.get(
                "discordUsersInVoice"
            )
            waywo_post_id = validation_serializer.data.get("waywoPostId")
            account_ids_to_beans_awarded = {}

            # Locate the correct PathfinderHikeSubmission
            try:
                hike_submission = PathfinderHikeSubmission.objects.filter(
                    waywo_post_id=waywo_post_id, playtest_game_id__isnull=True
                ).get()
            except PathfinderHikeSubmission.DoesNotExist:
                raise PermissionDenied(
                    "Could not find an incomplete Pathfinder Hike Submission associated with this WAYWO Post."
                )

            # Save the PathfinderHikeSubmission to automatically create PathfinderHikeGameParticipation records
            hike_submission.playtest_game_id = playtest_game_id
            hike_submission.save()

            # Save records for every DiscordAccount represented in `discord_users_in_voice`
            discord_accounts = []
            for discord_user in discord_users_in_voice:
                try:
                    discord_account = update_or_create_discord_account(
                        discord_user.get("discordId"),
                        discord_user.get("discordUsername"),
                        request.user,
                    )
                except Exception as ex:
                    logger.error(ex)
                    raise APIException(
                        "Error attempting to complete a Pathfinder Hike Submission."
                    )
                discord_accounts.append(discord_account)
            for discord_account in discord_accounts:
                PathfinderHikeVoiceParticipation.objects.create(
                    creator=request.user,
                    hike_submission=hike_submission,
                    discord=discord_account,
                )

            # Award Pathfinder Beans
            for game_participation in PathfinderHikeGameParticipation.objects.filter(
                hike_submission=hike_submission
            ):
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        xbox_live_account_id=game_participation.xuid
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    continue
                if link.discord_account_id not in account_ids_to_beans_awarded:
                    account_ids_to_beans_awarded[link.discord_account_id] = 0
                account_ids_to_beans_awarded[
                    link.discord_account_id
                ] += BEAN_AWARD_HIKE_GAME_PARTICIPATION
            for voice_participation in PathfinderHikeVoiceParticipation.objects.filter(
                hike_submission=hike_submission
            ):
                if voice_participation.discord_id not in account_ids_to_beans_awarded:
                    account_ids_to_beans_awarded[voice_participation.discord_id] = 0
                account_ids_to_beans_awarded[
                    voice_participation.discord_id
                ] += BEAN_AWARD_HIKE_VOICE_PARTICIPATION
            awarded_users = []
            for discord_id in account_ids_to_beans_awarded:
                beans_to_award = account_ids_to_beans_awarded[discord_id]
                discord_account = DiscordAccount.objects.get(discord_id=discord_id)
                success = change_beans(discord_account, beans_to_award)
                awarded_users.append(
                    DiscordUserAwardedBeansSerializer(
                        {
                            "discordId": discord_account.discord_id,
                            "discordUsername": discord_account.discord_username,
                            "awardedBeans": beans_to_award if success else 0,
                        }
                    ).data
                )
            awarded_users.sort(key=lambda x: x["awardedBeans"], reverse=True)

            # Return a list of those who were awarded Beans
            serializer = HikeCompletePostResponseSerializer(
                {
                    "success": True,
                    "awardedUsers": awarded_users,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


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
                playtest_game_id__isnull=True,
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
                        "mode": submission.mode,
                    }
                )
            unscheduled_incomplete_submissions = (
                PathfinderHikeSubmission.objects.filter(
                    playtest_game_id__isnull=True,
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
                        "mode": submission.mode,
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
            mode = validation_serializer.data.get("mode")
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
            bean_count = check_beans(map_submitter_discord)
            if bean_count < BEAN_COST_HIKE_SUBMISSION:
                raise PermissionDenied(
                    "This Discord user does not have enough Pathfinder Beans for a Hike submission."
                )
            incomplete_hikes_for_post_id = PathfinderHikeSubmission.objects.filter(
                playtest_game_id__isnull=True,
                waywo_post_id=waywo_post_id,
            )
            if len(incomplete_hikes_for_post_id) > 0:
                raise PermissionDenied(
                    "A Pathfinder Hike submission already exists for this post."
                )
            # Try subtracting the beans, and create the submission if it works
            try:
                if change_beans(map_submitter_discord, -1 * BEAN_COST_HIKE_SUBMISSION):
                    PathfinderHikeSubmission.objects.create(
                        creator=request.user,
                        waywo_post_title=waywo_post_title,
                        waywo_post_id=waywo_post_id,
                        map_submitter_discord=map_submitter_discord,
                        max_player_count=max_player_count,
                        map=map,
                        mode=mode,
                    )
                else:
                    raise Exception("Failed to change bean count.")
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a PathfinderHikeSubmission."
                )
            serializer = HikeSubmissionPostResponseSerializer({"success": True})
            return Response(serializer.data, status=status.HTTP_200_OK)


class PathfinderProdigyCheckView(APIView):
    @extend_schema(
        request=PathfinderProdigyCheckRequestSerializer,
        responses={
            200: PathfinderProdigyCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API, and returning a payload indicating whether or not each one qualifies for Trailblazer Titan.
        """
        validation_serializer = PathfinderProdigyCheckRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            try:
                # Get the XUIDs from all verified DiscordXboxLiveLink records matching the input discordUserIDs
                links = (
                    DiscordXboxLiveLink.objects.filter(
                        discord_account_id__in=discord_ids
                    )
                    .filter(verified=True)
                    .order_by("created_at")
                )
                xuid_to_discord_id = {
                    link.xbox_live_account_id: link.discord_account_id for link in links
                }
                xuids = [link.xbox_live_account_id for link in links]

                # Update known playlists
                update_known_playlists()

                # Get contributor XUIDs for all maps in all active playlists
                contributor_xuids = get_contributor_xuids_for_maps_in_active_playlists()
                logger.info(contributor_xuids)

                # For each Pathfinder XUID, add Discord IDs to the appropriate yes/no list
                linked_discord_ids = set()
                yes = []
                no = []
                for xuid in xuids:
                    discord_id = xuid_to_discord_id.get(xuid)
                    linked_discord_ids.add(discord_id)
                    if xuid in contributor_xuids:
                        yes.append(
                            PathfinderProdigyCheckSerializer(
                                {
                                    "discordUserId": discord_id,
                                }
                            ).data
                        )
                    else:
                        no.append(
                            PathfinderProdigyCheckSerializer(
                                {
                                    "discordUserId": discord_id,
                                }
                            ).data
                        )

                # For Discord IDs without linked gamertags, automatically add them to the no list
                unlinked_discord_ids = set(discord_ids).difference(linked_discord_ids)
                for discord_id in unlinked_discord_ids:
                    no.append(
                        PathfinderProdigyCheckSerializer(
                            {
                                "discordUserId": discord_id,
                            }
                        ).data
                    )
            except Exception as ex:
                logger.error("Error attempting the Pathfinder Prodigy check.")
                logger.error(ex)
                raise APIException("Error attempting the Pathfinder Prodigy check.")
            serializer = PathfinderProdigyCheckResponseSerializer(
                {
                    "yes": yes,
                    "no": no,
                }
            )
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


class PathfinderWAYWOCommentView(APIView):
    @extend_schema(
        request=WAYWOCommentRequestSerializer,
        responses={
            200: WAYWOCommentResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Record that someone has made a WAYWO post.
        """
        validation_serializer = WAYWOCommentRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            commenter_discord_id = validation_serializer.data.get("commenterDiscordId")
            commenter_discord_username = validation_serializer.data.get(
                "commenterDiscordUsername"
            )
            post_id = validation_serializer.data.get("postId")
            comment_id = validation_serializer.data.get("commentId")
            comment_length = validation_serializer.data.get("commentLength")
            try:
                commenter_discord = update_or_create_discord_account(
                    commenter_discord_id, commenter_discord_username, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to record a PathfinderWAYWOComment."
                )
            existing_qualified_comments = PathfinderWAYWOComment.objects.filter(
                commenter_discord=commenter_discord,
                post_id=post_id,
                comment_length__gte=100,
            ).count()
            commenter_is_op = (
                PathfinderWAYWOPost.objects.filter(
                    poster_discord=commenter_discord, post_id=post_id
                ).count()
                != 0
            )
            awarded_bean = False
            try:
                PathfinderWAYWOComment.objects.create(
                    creator=request.user,
                    commenter_discord=commenter_discord,
                    post_id=post_id,
                    comment_id=comment_id,
                    comment_length=comment_length,
                )
                if (
                    existing_qualified_comments == 0
                    and not commenter_is_op
                    and comment_length
                    >= PATHFINDER_WAYWO_COMMENT_MIN_LENGTH_FOR_BEAN_AWARD
                ):
                    awarded_bean = change_beans(
                        commenter_discord, BEAN_AWARD_WAYWO_COMMENT
                    )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a PathfinderWAYWOComment."
                )
            serializer = WAYWOCommentResponseSerializer(
                {"success": True, "awardedBean": awarded_bean}
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
                # Get the Season or Era
                season_id = None
                era = None
                try:
                    season_id = get_current_season_id()
                except MissingSeasonDataException:
                    pass
                try:
                    era = get_current_era()
                except MissingEraDataException:
                    pass
                assert season_id is not None or era is not None
                assert season_id is None or era is None

                # Upsert the DiscordAccount & find a link record
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
                elif season_id == "5":
                    serializer_class = PathfinderDynamoSeason5ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s5_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsBeanSpender"] = discord_earns.get(
                        "bean_spender", 0
                    )
                    serializable_dict["pointsWhatAreYouWorkingOn"] = discord_earns.get(
                        "what_are_you_working_on", 0
                    )
                    serializable_dict["pointsFeedbackFiend"] = discord_earns.get(
                        "feedback_fiend", 0
                    )

                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s5_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsGoneHiking"] = xbox_earns.get(
                        "gone_hiking", 0
                    )
                    serializable_dict["pointsForgedInFire"] = xbox_earns.get(
                        "forged_in_fire", 0
                    )
                elif era == 1:
                    serializer_class = PathfinderDynamoEra1ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_e1_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsBeanSpender"] = discord_earns.get(
                        "bean_spender", 0
                    )
                    serializable_dict["pointsWhatAreYouWorkingOn"] = discord_earns.get(
                        "what_are_you_working_on", 0
                    )
                    serializable_dict["pointsFeedbackFiend"] = discord_earns.get(
                        "feedback_fiend", 0
                    )

                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_e1_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsGoneHiking"] = xbox_earns.get(
                        "gone_hiking", 0
                    )
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


class PopularFilesView(APIView):
    @extend_schema(
        responses={
            200: PopularFilesResponseSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            404: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the 10 files tagged with 'HaloFunTime' with the most recent plays.
        """
        try:
            import json

            hft_popular_files = search_halofuntime_popular()
            xuids = set()
            for file in hft_popular_files:
                file_contributors = file.get("Contributors")
                for contributor in file_contributors:
                    xuids.add(int(contributor.lstrip("xuid(").rstrip(")")))
            links = DiscordXboxLiveLink.objects.filter(xbox_live_account_id__in=xuids)
            xuid_to_discord_id = {
                link.xbox_live_account_id: link.discord_account_id for link in links
            }
            logger.info(json.dumps(hft_popular_files))
            files = []
            for file in hft_popular_files:
                file_contributors = file.get("Contributors")
                contributor_discord_ids = []
                for contributor in file_contributors:
                    contributor_discord_id = xuid_to_discord_id.get(
                        int(contributor.lstrip("xuid(").rstrip(")"))
                    )
                    if contributor_discord_id is not None:
                        contributor_discord_ids.append(contributor_discord_id)
                files.append(
                    PopularFileSerializer(
                        {
                            "assetId": file.get("AssetId"),
                            "versionId": file.get("AssetVersionId"),
                            "fileType": SEARCH_ASSET_KINDS.get(
                                file.get("AssetKind", 0)
                            ),
                            "name": file.get("Name"),
                            "description": file.get("Description"),
                            "playsRecent": file.get("PlaysRecent"),
                            "playsAllTime": file.get("PlaysAllTime"),
                            "thumbnailUrl": file.get("ThumbnailUrl"),
                            "waypointUrl": get_waypoint_file_url(file),
                            "bookmarks": file.get("Likes"),
                            "contributorDiscordIds": contributor_discord_ids,
                            "tags": file.get("Tags", []),
                            "averageRating": file.get("AverageRating"),
                            "numberOfRatings": file.get("NumberOfRatings"),
                        }
                    ).data
                )
        except Exception as ex:
            logger.error(ex)
            raise APIException("Could not get popular files.")

        serializer = PopularFilesResponseSerializer({"files": files})
        return Response(serializer.data, status=status.HTTP_200_OK)


class WeeklyRecapView(APIView):
    @extend_schema(
        request=WeeklyRecapRequestSerializer,
        responses={
            200: WeeklyRecapResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Retrieve data for the Pathfinder club weekly recap.
        """
        validation_serializer = WeeklyRecapRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_users_awarded_beans = validation_serializer.data.get(
                "discordUsersAwardedBeans"
            )
            # Award Beans as instructed
            for discord_user in discord_users_awarded_beans:
                try:
                    discord_account = update_or_create_discord_account(
                        discord_user.get("discordId"),
                        discord_user.get("discordUsername"),
                        request.user,
                    )
                    success = change_beans(
                        discord_account, discord_user.get("awardedBeans")
                    )
                    assert success
                except Exception as ex:
                    logger.error(ex)
                    raise APIException("Error attempting the Pathfinder Weekly Recap.")
            # Return weekly recap data
            end_time = now_utc()
            start_time = end_time + datetime.timedelta(days=-7)
            serializer = WeeklyRecapResponseSerializer(
                {
                    "hikerCount": PathfinderHikeGameParticipation.objects.filter(
                        created_at__range=[start_time, end_time]
                    )
                    .values("xuid")
                    .distinct()
                    .count(),
                    "hikeSubmissionCount": PathfinderHikeSubmission.objects.filter(
                        created_at__range=[start_time, end_time]
                    ).count(),
                    "waywoCommentCount": PathfinderWAYWOComment.objects.filter(
                        created_at__range=[start_time, end_time]
                    ).count(),
                    "waywoPostCount": PathfinderWAYWOPost.objects.filter(
                        created_at__range=[start_time, end_time]
                    ).count(),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
