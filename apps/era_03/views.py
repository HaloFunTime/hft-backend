import datetime
import logging

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.era_03.models import BoatCaptain, BoatDeckhand, BoatRank
from apps.era_03.serializers import (
    BoardBoatRequestSerializer,
    BoardBoatResponseSerializer,
    CheckDeckhandGamesRequestSerializer,
    CheckDeckhandGamesResponseSerializer,
    SaveBoatCaptainRequestSerializer,
    SaveBoatCaptainResponseSerializer,
)
from apps.era_03.utils import fetch_match_ids_for_xuid, save_new_matches
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
