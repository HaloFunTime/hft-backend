import datetime
import logging

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.era_02.models import MVT
from apps.era_02.serializers import (
    CheckPlayerGamesRequestSerializer,
    CheckPlayerGamesResponseSerializer,
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
                )
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
