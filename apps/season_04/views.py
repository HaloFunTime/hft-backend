import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.link.models import DiscordXboxLiveLink
from apps.season_04.serializers import (
    CheckStampsRequestSerializer,
    CheckStampsResponseSerializer,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CheckStampsView(APIView):
    @extend_schema(
        request=CheckStampsRequestSerializer,
        responses={
            200: CheckStampsResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a Discord User ID by retrieving its verified linked Xbox Live gamertag, querying stats from the Halo
        Infinite API and the HFT DB, and returning a payload indicating the progress the gamertag has made toward the
        Season 4 Stamp Challenge.
        """
        validation_serializer = CheckStampsRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            funtimer_rank = validation_serializer.data.get("funTimerRank")
            invite_uses = validation_serializer.data.get("inviteUses")
            stamps_completed = 0
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                # TODO: Check challenges 1-5 here
                if funtimer_rank >= 5:
                    stamps_completed += 1
                if invite_uses > 0:
                    stamps_completed += 1
                link = None
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_account.discord_id, verified=True
                    ).get()
                except DiscordXboxLiveLink.DoesNotExist:
                    pass

                if link is not None:
                    # TODO: Check challenges 6-10 here
                    # TODO: Check challenges 11-15 here
                    # TODO: Check challenges 16-20 here
                    pass
            except Exception as ex:
                logger.error("Error attempting to check Stamp Challenge progress.")
                logger.error(ex)
                raise APIException(
                    "Error attempting to check Stamp Challenge progress."
                )
            serializer = CheckStampsResponseSerializer(
                {
                    "linkedGamertag": link is not None,
                    "stampsCompleted": stamps_completed,
                    "scoreChatterbox": funtimer_rank,
                    "scoreFuntagious": invite_uses,
                    "scoreReppingIt": -1,
                    "scoreFundurance": -1,
                    "scoreGangsAllHere": -1,
                    "scoreStackingDubs": -1,
                    "scoreLicenseToKill": -1,
                    "scoreAimForTheHead": -1,
                    "scorePowerTrip": -1,
                    "scoreBotBullying": -1,
                    "scoreOneFundo": -1,
                    "scoreGleeFiddy": -1,
                    "scoreWellTraveled": -1,
                    "scoreMoModesMoFun": -1,
                    "scorePackedHouse": -1,
                    "completedFinishInFive": False,
                    "completedVictoryLap": False,
                    "completedATeam": False,
                    "completedSneedsSeedGreed": False,
                    "completedFuckThatGuy": False,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
