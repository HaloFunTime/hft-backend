import datetime
import logging

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.era_03.exceptions import (
    AlreadyRank10Exception,
    AssignmentsIncompleteException,
)
from apps.era_03.models import (
    BoatCaptain,
    BoatDeckhand,
    BoatRank,
    BoatSecret,
    BoatSecretUnlock,
    WeeklyBoatAssignments,
)
from apps.era_03.serializers import (
    BoardBoatRequestSerializer,
    BoardBoatResponseSerializer,
    CheckBoatAssignmentsRequestSerializer,
    CheckBoatAssignmentsResponseSerializer,
    CheckDeckhandGamesRequestSerializer,
    CheckDeckhandGamesResponseSerializer,
    SaveBoatCaptainRequestSerializer,
    SaveBoatCaptainResponseSerializer,
)
from apps.era_03.utils import (
    check_deckhand_promotion,
    check_xuid_assignment,
    check_xuid_secret,
    fetch_match_ids_for_xuid,
    generate_weekly_assignments,
    get_current_week_start,
    save_new_matches,
)
from apps.halo_infinite.constants import ERA_3_END_TIME, ERA_3_START_TIME
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.link.models import DiscordXboxLiveLink
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class BoardBoat(APIView):
    @extend_schema(
        request=BoardBoatRequestSerializer,
        responses={
            200: BoardBoatResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Create a BoatDeckhand record for someone who has not yet joined the Era 3 Boat Challenge.
        """
        validation_serializer = BoardBoatRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")

            try:
                deckhand = BoatDeckhand.objects.filter(deckhand_id=discord_id).get()
            except BoatDeckhand.DoesNotExist:
                deckhand = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                new_joiner = False
                if deckhand is None:
                    new_joiner = True
                    deckhand = BoatDeckhand.objects.create(
                        creator=request.user,
                        deckhand=discord_account,
                        rank=BoatRank.objects.filter(tier=1).get(),
                    )

            except Exception as ex:
                logger.error("Error attempting to save a Boat Challenge Deckhand.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to save a Boat Challenge Deckhand."
                )
            serializer = BoardBoatResponseSerializer(
                {
                    "rank": deckhand.rank.rank,
                    "discordUserId": deckhand.deckhand_id,
                    "newJoiner": new_joiner,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class CheckBoatAssignments(APIView):
    @extend_schema(
        request=CheckBoatAssignmentsRequestSerializer,
        responses={
            200: CheckBoatAssignmentsResponseSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Check if a BoatDeckhand has completed their assignments for the week.
        """
        validation_serializer = CheckBoatAssignmentsRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            joined_challenge = False
            linked_gamertag = False
            current_rank = "N/A"
            current_rank_tier = 0
            secrets_unlocked = []
            existing_assignments = False
            weekly_assignments = None
            assignment_1 = None
            assignment_2 = None
            assignment_3 = None
            assignments_completed = False
            just_promoted = False

            current_week_start = get_current_week_start()

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                deckhand = BoatDeckhand.objects.filter(
                    deckhand_id=discord_account.discord_id
                ).get()
                joined_challenge = True

                link = DiscordXboxLiveLink.objects.filter(
                    discord_account_id=discord_account.discord_id, verified=True
                ).get()
                linked_gamertag = True

                current_rank = deckhand.rank.rank
                current_rank_tier = deckhand.rank.tier
                if current_rank_tier >= 6:
                    # Retrieve all Boat Secrets this participant has already unlocked
                    secrets_unlocked.extend(
                        [
                            {
                                "title": secret_unlocked.secret.title,
                                "hint": secret_unlocked.secret.hint,
                                "matchId": secret_unlocked.match_id,
                                "newlyUnlocked": False,
                            }
                            for secret_unlocked in deckhand.secrets_unlocked.all()
                        ]
                    )

                    # Evaluate all Boat Secrets this participant has not yet unlocked
                    for secret in BoatSecret.objects.exclude(
                        medal_id__in=[
                            secret_unlocked.secret.medal_id
                            for secret_unlocked in deckhand.secrets_unlocked.all()
                        ]
                    ):
                        match = check_xuid_secret(
                            link.xbox_live_account_id, secret, current_week_start
                        )
                        if match is not None:
                            BoatSecretUnlock.objects.create(
                                secret=secret,
                                deckhand=deckhand,
                                match=match,
                                creator=request.user,
                            )
                            secrets_unlocked.append(
                                {
                                    "title": secret.title,
                                    "hint": secret.hint,
                                    "matchId": match.match_id,
                                    "newlyUnlocked": True,
                                }
                            )

                if current_rank_tier >= 10:
                    raise AlreadyRank10Exception()

                weekly_assignments = WeeklyBoatAssignments.objects.filter(
                    deckhand=deckhand, week_start=current_week_start
                ).get()
                existing_assignments = True

                # Evaluate all BoatAssignments for this deckhand for this week
                assignment_1 = (
                    weekly_assignments.assignment_1.description
                    if weekly_assignments.assignment_1 is not None
                    else None
                )
                assignment_2 = (
                    weekly_assignments.assignment_2.description
                    if weekly_assignments.assignment_2 is not None
                    else None
                )
                assignment_3 = (
                    weekly_assignments.assignment_3.description
                    if weekly_assignments.assignment_3 is not None
                    else None
                )
                if (
                    weekly_assignments.assignment_1 is not None
                    and weekly_assignments.assignment_1_completion_match_id is None
                ):
                    match = check_xuid_assignment(
                        link.xbox_live_account_id,
                        weekly_assignments.assignment_1,
                        current_week_start,
                    )
                    if match is not None:
                        weekly_assignments.assignment_1_completion_match_id = (
                            match.match_id
                        )
                if (
                    weekly_assignments.assignment_2 is not None
                    and weekly_assignments.assignment_2_completion_match_id is None
                ):
                    match = check_xuid_assignment(
                        link.xbox_live_account_id,
                        weekly_assignments.assignment_2,
                        current_week_start,
                    )
                    if match is not None:
                        weekly_assignments.assignment_2_completion_match_id = (
                            match.match_id
                        )
                if (
                    weekly_assignments.assignment_3 is not None
                    and weekly_assignments.assignment_3_completion_match_id is None
                ):
                    match = check_xuid_assignment(
                        link.xbox_live_account_id,
                        weekly_assignments.assignment_3,
                        current_week_start,
                    )
                    if match is not None:
                        weekly_assignments.assignment_3_completion_match_id = (
                            match.match_id
                        )
                weekly_assignments.save()
                if not weekly_assignments.completed_all_assignments:
                    raise AssignmentsIncompleteException()
                assignments_completed = True

                # Promote deckhand if they have not already been promoted this week
                just_promoted = check_deckhand_promotion(deckhand, weekly_assignments)
                current_rank = deckhand.rank.rank
                current_rank_tier = deckhand.rank.tier
            except BoatDeckhand.DoesNotExist:
                logger.info("No BoatDeckhand exists.")
            except DiscordXboxLiveLink.DoesNotExist:
                logger.info("No DiscordXboxLiveLink exists.")
            except AlreadyRank10Exception:
                logger.info("Deckhand is already at rank 10.")
            except WeeklyBoatAssignments.DoesNotExist:
                logger.info("No assignments exist for this week.")
                weekly_assignments = generate_weekly_assignments(
                    deckhand, current_week_start, request.user
                )
                assignment_1 = weekly_assignments.assignment_1.description
                assignment_2 = (
                    weekly_assignments.assignment_2.description
                    if weekly_assignments.assignment_2 is not None
                    else None
                )
                assignment_3 = (
                    weekly_assignments.assignment_3.description
                    if weekly_assignments.assignment_3 is not None
                    else None
                )
            except AssignmentsIncompleteException:
                logger.info("Assignments are incomplete.")
            except Exception as ex:
                import traceback

                traceback.print_exc()
                logger.error("Error attempting to check Boat Challenge assignments.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Boat Challenge assignments."
                )
            finally:
                assignment_1_completed = (
                    weekly_assignments is not None
                    and weekly_assignments.assignment_1_completion_match_id is not None
                )
                assignment_2_completed = (
                    weekly_assignments is not None
                    and weekly_assignments.assignment_2_completion_match_id is not None
                )
                assignment_3_completed = (
                    weekly_assignments is not None
                    and weekly_assignments.assignment_3_completion_match_id is not None
                )
                serializer = CheckBoatAssignmentsResponseSerializer(
                    {
                        "discordUserId": discord_id,
                        "joinedChallenge": joined_challenge,
                        "linkedGamertag": linked_gamertag,
                        "currentRank": current_rank,
                        "currentRankTier": current_rank_tier,
                        "assignment1": assignment_1,
                        "assignment1Completed": assignment_1_completed,
                        "assignment2": assignment_2,
                        "assignment2Completed": assignment_2_completed,
                        "assignment3": assignment_3,
                        "assignment3Completed": assignment_3_completed,
                        "assignmentsCompleted": assignments_completed,
                        "existingAssignments": existing_assignments,
                        "justPromoted": just_promoted,
                        "secretsUnlocked": secrets_unlocked,
                    }
                )
            return Response(serializer.data, status=status.HTTP_200_OK)


class CheckDeckhandGames(APIView):
    @extend_schema(
        request=CheckDeckhandGamesRequestSerializer,
        responses={
            200: CheckDeckhandGamesResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Retrieve Halo Infinite games for each BoatDeckhand's linked gamertag.
        """
        validation_serializer = CheckDeckhandGamesRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            try:
                deckhands = BoatDeckhand.objects.filter(deckhand_id__in=discord_ids)
                deckhand_ids = [deckhand.deckhand_id for deckhand in deckhands]
                links = DiscordXboxLiveLink.objects.filter(
                    verified=True, discord_account_id__in=deckhand_ids
                )
                discord_ids_to_xuids = {}
                for link in links:
                    discord_ids_to_xuids[
                        link.discord_account_id
                    ] = link.xbox_live_account_id
                deckhand_match_ids = set()
                with requests.Session() as s:
                    for deckhand in deckhands:
                        deckhand_xuid = discord_ids_to_xuids.get(
                            deckhand.deckhand_id, None
                        )
                        if deckhand_xuid is not None:
                            match_ids = fetch_match_ids_for_xuid(deckhand_xuid, s)
                            deckhand.most_recent_match_id = (
                                None if not match_ids else match_ids[0]
                            )
                            deckhand.save()
                            deckhand_match_ids |= set(match_ids)
                old_match_ids = {
                    str(uuid)
                    for uuid in HaloInfiniteMatch.objects.filter(
                        start_time__gte=ERA_3_START_TIME, end_time__lte=ERA_3_END_TIME
                    ).values_list("match_id", flat=True)
                }
                new_match_ids = deckhand_match_ids.difference(old_match_ids)
                new_matches_saved = save_new_matches(new_match_ids, request.user)
            except Exception as ex:
                logger.error("Error attempting to check Boat Challenge Deckhand games.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Boat Challenge Deckhand games."
                )
            serializer = CheckDeckhandGamesResponseSerializer(
                {
                    "success": new_matches_saved,
                    "totalGameCount": len(deckhand_match_ids),
                    "newGameCount": len(new_match_ids),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class SaveBoatCaptain(APIView):
    @extend_schema(
        request=SaveBoatCaptainRequestSerializer,
        responses={
            200: SaveBoatCaptainResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Save whether a Discord User ID has already completed the Era 3 Boat Challenge. Update or create a record
        in the BoatCaptain table based on that information.
        """
        validation_serializer = SaveBoatCaptainRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            rank_tier = validation_serializer.data.get("rankTier")

            try:
                existing_boat_captain = BoatCaptain.objects.filter(
                    earner_id=discord_id
                ).get()
            except BoatCaptain.DoesNotExist:
                existing_boat_captain = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                if existing_boat_captain is None:
                    BoatCaptain.objects.create(
                        creator=request.user,
                        earner=discord_account,
                        earned_at=datetime.datetime.now(tz=datetime.timezone.utc),
                        rank_tier=rank_tier,
                    )
                else:
                    existing_boat_captain.rank_tier = rank_tier
                    existing_boat_captain.save()

            except Exception as ex:
                logger.error("Error attempting to save a Boat Captain.")
                logger.error(ex)
                raise APIException("Error attempting to save a Boat Captain.")
            serializer = SaveBoatCaptainResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "newBoatCaptain": existing_boat_captain is None,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
