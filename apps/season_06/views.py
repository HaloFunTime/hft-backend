import datetime
import logging
import random

import requests
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.link.models import DiscordXboxLiveLink
from apps.season_06.constants import LETTERS_25
from apps.season_06.models import BingoBuff, BingoChallengeParticipant
from apps.season_06.serializers import (
    CheckParticipantGamesRequestSerializer,
    CheckParticipantGamesResponseSerializer,
    JoinChallengeRequestSerializer,
    JoinChallengeResponseSerializer,
    SaveBuffRequestSerializer,
    SaveBuffResponseSerializer,
)
from apps.season_06.utils import fetch_match_ids_for_xuid, save_new_matches
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CheckBingoCard(APIView):
    pass


class CheckParticipantGames(APIView):
    @extend_schema(
        request=CheckParticipantGamesRequestSerializer,
        responses={
            200: CheckParticipantGamesResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Retrieve Halo Infinite games for each BingoChallengeParticipant's linked gamertag.
        """
        validation_serializer = CheckParticipantGamesRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            # Should receive Discord IDs for all active server members
            discord_ids = validation_serializer.data.get("discordUserIds")
            try:
                participants = BingoChallengeParticipant.objects.filter(
                    participant_id__in=discord_ids
                )
                participant_ids = [
                    participant.participant_id for participant in participants
                ]
                links = DiscordXboxLiveLink.objects.filter(
                    verified=True, discord_account_id__in=participant_ids
                )
                discord_ids_to_xuids = {}
                for link in links:
                    discord_ids_to_xuids[
                        link.discord_account_id
                    ] = link.xbox_live_account_id
                with requests.Session() as s:
                    participant_match_ids = set()
                    for participant in participants:
                        participant_xuid = discord_ids_to_xuids.get(
                            participant.participant_id, None
                        )
                        if participant_xuid is not None:
                            match_ids = fetch_match_ids_for_xuid(participant_xuid, s)
                            participant.most_recent_match_id = (
                                None if not match_ids else match_ids[0]
                            )
                            participant.save()
                            participant_match_ids |= set(match_ids)
                old_match_ids = {
                    str(uuid)
                    for uuid in HaloInfiniteMatch.objects.all().values_list(
                        "match_id", flat=True
                    )
                }
                new_match_ids = participant_match_ids.difference(old_match_ids)
                new_matches_saved = save_new_matches(new_match_ids, request.user)
            except Exception as ex:
                logger.error(
                    "Error attempting to check Bingo Challenge Participant games."
                )
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Bingo Challenge Participant games."
                )
            serializer = CheckParticipantGamesResponseSerializer(
                {
                    "success": new_matches_saved,
                    "totalGameCount": len(participant_match_ids),
                    "newGameCount": len(new_match_ids),
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class JoinChallenge(APIView):
    @extend_schema(
        request=JoinChallengeRequestSerializer,
        responses={
            200: JoinChallengeResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Create a BingoChallengeParticipant for someone who has not yet joined the Season 6 Bingo Challenge.
        """
        validation_serializer = JoinChallengeRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")

            try:
                participant = BingoChallengeParticipant.objects.filter(
                    participant_id=discord_id
                ).get()
            except BingoChallengeParticipant.DoesNotExist:
                participant = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                new_joiner = False
                if participant is None:
                    new_joiner = True
                    randomized_letters = list(LETTERS_25)
                    random.shuffle(randomized_letters)
                    participant = BingoChallengeParticipant.objects.create(
                        creator=request.user,
                        participant=discord_account,
                        board_order="".join(randomized_letters),
                    )

            except Exception as ex:
                logger.error("Error attempting to save a Bingo Challenge Participant.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to save a Bingo Challenge Participant."
                )
            serializer = JoinChallengeResponseSerializer(
                {
                    "boardOrder": participant.board_order,
                    "discordUserId": participant.participant_id,
                    "newJoiner": new_joiner,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class SaveBuff(APIView):
    @extend_schema(
        request=SaveBuffRequestSerializer,
        responses={
            200: SaveBuffResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Save whether a Discord User ID has already completed the Season 6 Bingo Challenge. Update or create a record
        in the BingoBuff table based on that information.
        """
        validation_serializer = SaveBuffRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            bingo_count = validation_serializer.data.get("bingoCount")
            challenge_count = validation_serializer.data.get("challengeCount")

            try:
                existing_buff = BingoBuff.objects.filter(earner_id=discord_id).get()
            except BingoBuff.DoesNotExist:
                existing_buff = None

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                if existing_buff is None:
                    BingoBuff.objects.create(
                        creator=request.user,
                        earner=discord_account,
                        earned_at=datetime.datetime.now(tz=datetime.timezone.utc),
                        bingo_count=bingo_count,
                        challenge_count=challenge_count,
                    )
                else:
                    existing_buff.bingo_count = bingo_count
                    existing_buff.challenge_count = challenge_count
                    existing_buff.save()

            except Exception as ex:
                logger.error("Error attempting to save a Bingo Buff.")
                logger.error(ex)
                raise APIException("Error attempting to save a Bingo Buff.")
            serializer = SaveBuffResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "newBuff": existing_buff is None,
                    "blackout": bingo_count == 12 and challenge_count == 25,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
