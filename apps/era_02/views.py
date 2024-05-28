import datetime
import logging

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.era_02.models import MVT, TeamUpChallengeCompletion, TeamUpChallenges
from apps.era_02.serializers import (
    CheckPlayerGamesRequestSerializer,
    CheckPlayerGamesResponseSerializer,
    CheckTeamUpChallengesRequestSerializer,
    CheckTeamUpChallengesResponseSerializer,
    SaveMVTRequestSerializer,
    SaveMVTResponseSerializer,
)
from apps.era_02.utils import fetch_match_ids_for_xuid, save_new_matches
from apps.halo_infinite.constants import ERA_2_END_TIME, ERA_2_START_TIME
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.link.models import DiscordXboxLiveLink
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CheckPlayerGames(APIView):
    @extend_schema(
        request=CheckPlayerGamesRequestSerializer,
        responses={
            200: CheckPlayerGamesResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Retrieve Era 2 Halo Infinite games for the Discord account's linked gamertag.
        """
        validation_serializer = CheckPlayerGamesRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            # Should receive one Discord ID for all active server members
            discord_id = validation_serializer.data.get("discordUserId")
            try:
                link = DiscordXboxLiveLink.objects.filter(
                    verified=True, discord_account_id=discord_id
                ).first()
                fetched_match_ids = set()
                with requests.Session() as s:
                    if link is not None:
                        fetched_match_ids |= set(
                            fetch_match_ids_for_xuid(link.xbox_live_account_id, s)
                        )
                old_match_ids = {
                    str(uuid)
                    for uuid in HaloInfiniteMatch.objects.filter(
                        start_time__gte=ERA_2_START_TIME, end_time__lte=ERA_2_END_TIME
                    ).values_list("match_id", flat=True)
                }
                new_match_ids = fetched_match_ids.difference(old_match_ids)
                new_matches_saved = save_new_matches(new_match_ids, request.user)
            except Exception as ex:
                logger.error(
                    "Error attempting to check games for the Team Up Challenge."
                )
                logger.error(ex)
                raise APIException(
                    "Error attempting to check games for the Team Up Challenge."
                )
            serializer = CheckPlayerGamesResponseSerializer(
                {
                    "success": new_matches_saved,
                    "totalGameCount": len(fetched_match_ids),
                    "newGameCount": len(new_match_ids),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class CheckTeamUpChallenges(APIView):
    @extend_schema(
        request=CheckTeamUpChallengesRequestSerializer,
        responses={
            200: CheckTeamUpChallengesResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a Discord User ID by retrieving its verified linked Xbox Live gamertag, querying match stats from the
        HFT DB, and saving/returning the progress the gamertag has made toward the Era 2 Team Up Challenge.
        """
        validation_serializer = CheckTeamUpChallengesRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            link = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    pass

                completions_bait_the_flags = 0
                completions_forty_fists = 0
                completions_grenade_parade = 0
                completions_hundred_heads = 0
                completions_marks_of_shame = 0
                completions_most_valuable_driver = 0
                completions_own_the_zones = 0
                completions_speed_for_seeds = 0
                completions_spin_class = 0
                completions_summon_a_demon = 0
                if link is not None:
                    completions_bait_the_flags = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.BAIT_THE_FLAGS,
                        )
                    )
                    completions_forty_fists = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.FORTY_FISTS,
                        )
                    )
                    completions_grenade_parade = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.GRENADE_PARADE,
                        )
                    )
                    completions_hundred_heads = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.HUNDRED_HEADS,
                        )
                    )
                    completions_marks_of_shame = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.MARKS_OF_SHAME,
                        )
                    )
                    completions_most_valuable_driver = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.MOST_VALUABLE_DRIVER,
                        )
                    )
                    completions_own_the_zones = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.OWN_THE_ZONES,
                        )
                    )
                    completions_speed_for_seeds = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.SPEED_FOR_SEEDS,
                        )
                    )
                    completions_spin_class = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.SPIN_CLASS,
                        )
                    )
                    completions_summon_a_demon = len(
                        TeamUpChallengeCompletion.objects.filter(
                            xuid=link.xbox_live_account_id,
                            challenge=TeamUpChallenges.SUMMON_A_DEMON,
                        )
                    )
            except Exception as ex:
                logger.error("Error attempting to check Team Up Challenge progress.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Team Up Challenge progress."
                )
            serializer = CheckTeamUpChallengesResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "linkedGamertag": link is not None,
                    "completionsBaitTheFlags": completions_bait_the_flags,
                    "completionsFortyFists": completions_forty_fists,
                    "completionsGrenadeParade": completions_grenade_parade,
                    "completionsHundredHeads": completions_hundred_heads,
                    "completionsMarksOfShame": completions_marks_of_shame,
                    "completionsMostValuableDriver": completions_most_valuable_driver,
                    "completionsOwnTheZones": completions_own_the_zones,
                    "completionsSpeedForSeeds": completions_speed_for_seeds,
                    "completionsSpinClass": completions_spin_class,
                    "completionsSummonADemon": completions_summon_a_demon,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class SaveMVT(APIView):
    @extend_schema(
        request=SaveMVTRequestSerializer,
        responses={
            200: SaveMVTResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Save whether a Discord User ID has already completed the Era 2 Team Up Challenge. Update or create a record
        in the MVT table based on that information.
        """
        validation_serializer = SaveMVTRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            mvt_points = validation_serializer.data.get("mvtPoints")
            newly_maxed = False

            try:
                existing_mvt = MVT.objects.filter(earner_id=discord_id).get()
            except MVT.DoesNotExist:
                existing_mvt = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                if existing_mvt is None:
                    MVT.objects.create(
                        creator=request.user,
                        earner=discord_account,
                        earned_at=datetime.datetime.now(tz=datetime.timezone.utc),
                        mvt_points=mvt_points,
                    )
                    newly_maxed = mvt_points == 250
                else:
                    newly_maxed = mvt_points == 250 and existing_mvt.mvt_points != 250
                    existing_mvt.mvt_points = mvt_points
                    existing_mvt.save()

            except Exception as ex:
                logger.error("Error attempting to save an MVT.")
                logger.error(ex)
                raise APIException("Error attempting to save an MVT.")
            serializer = SaveMVTResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "newMVT": existing_mvt is None,
                    "maxed": newly_maxed,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
