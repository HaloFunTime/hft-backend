import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.fun_time_friday.utils import get_voice_connections
from apps.halo_infinite.api.service_record import service_record
from apps.halo_infinite.constants import (
    MEDAL_ID_PERFECTION,
    PLAYLIST_ID_BOT_BOOTCAMP,
    SEASON_3_API_ID,
    SEASON_3_END_TIME,
    SEASON_3_START_TIME,
)
from apps.link.models import DiscordXboxLiveLink
from apps.reputation.models import PlusRep
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
            stamps_completed = 0
            score_chatterbox = 0
            score_funtagious = 0
            score_repping_it = 0
            score_fundurance = 0
            score_secret_socialite = 0
            score_stacking_dubs = 0
            score_license_to_kill = 0
            score_aim_for_the_head = 0
            score_power_trip = 0
            score_bot_bullying = 0
            score_one_fundo = -1
            score_glee_fiddy = -1
            score_well_traveled = -1
            score_mo_modes_mo_fun = -1
            score_epidemic = -1
            completed_finish_in_five = False
            completed_victory_lap = False
            completed_type_a = False
            completed_formerly_chucks = False
            completed_in_particular = False
            # TODO: Update the following variables for Season 4 when known
            season_start_time = SEASON_3_START_TIME
            season_end_time = SEASON_3_END_TIME
            season_api_id = SEASON_3_API_ID
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

                # HALOFUNTIME DISCORD CHALLENGES
                funtimer_rank = validation_serializer.data.get("funTimerRank")
                invite_uses = validation_serializer.data.get("inviteUses")
                voice_connections = get_voice_connections(
                    discord_account, season_start_time, season_end_time
                )
                societies_joined = validation_serializer.data.get("societiesJoined")
                # CHALLENGE #1: Chatterbox
                score_chatterbox = funtimer_rank
                if score_chatterbox >= 5:
                    stamps_completed += 1
                # CHALLENGE #2: Funtagious
                score_funtagious = invite_uses
                if score_funtagious >= 1:
                    stamps_completed += 1
                # CHALLENGE #3: Repping It
                score_repping_it = PlusRep.objects.filter(
                    giver=discord_account,
                    created_at__range=(season_start_time, season_end_time),
                ).count()
                if score_repping_it >= 10:
                    stamps_completed += 1
                # CHALLENGE #4: Fundurance
                if voice_connections:
                    max_connected_seconds = max(
                        voice_connections, key=lambda x: x.get("time_connected")
                    )["time_connected"].total_seconds()
                    score_fundurance = int(max_connected_seconds / 3600)
                if score_fundurance >= 3:
                    stamps_completed += 1
                # CHALLENGE #5: Secret Socialite
                score_secret_socialite = societies_joined
                if score_secret_socialite >= 1:
                    stamps_completed += 1

                if link is not None:
                    # HALO INFINITE MATCHMAKING CHALLENGES
                    season_sr = service_record(link.xbox_live_account_id, season_api_id)
                    bot_bootcamp_season_sr = service_record(
                        link.xbox_live_account_id,
                        season_api_id,
                        PLAYLIST_ID_BOT_BOOTCAMP,
                    )  # TODO: Update this for Season 4 when Season 4 API ID is known
                    medals = bot_bootcamp_season_sr.get("CoreStats").get("Medals")
                    medals_list = list(
                        filter(lambda x: x.get("NameId") == MEDAL_ID_PERFECTION, medals)
                    )
                    # CHALLENGE #6: Stacking Dubs
                    score_stacking_dubs = season_sr.get("Wins")
                    if score_stacking_dubs > 200:
                        stamps_completed += 1
                    # CHALLENGE #7: License to Kill
                    score_license_to_kill = season_sr.get("CoreStats").get("Kills")
                    if score_license_to_kill > 5000:
                        stamps_completed += 1
                    # CHALLENGE #8: Aim for the Head
                    score_aim_for_the_head = season_sr.get("CoreStats").get(
                        "HeadshotKills"
                    )
                    if score_aim_for_the_head > 3000:
                        stamps_completed += 1
                    # CHALLENGE #9: Power Trip
                    score_power_trip = season_sr.get("CoreStats").get(
                        "PowerWeaponKills"
                    )
                    if score_power_trip > 1500:
                        stamps_completed += 1
                    # CHALLENGE #10: Bot Bullying
                    score_bot_bullying = (
                        0 if len(medals_list) == 0 else medals_list[0].get("Count", 0)
                    )
                    if score_bot_bullying > 0:
                        stamps_completed += 1
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
                    "discordUserId": discord_id,
                    "stampsCompleted": stamps_completed,
                    "scoreChatterbox": score_chatterbox,
                    "scoreFuntagious": score_funtagious,
                    "scoreReppingIt": score_repping_it,
                    "scoreFundurance": score_fundurance,
                    "scoreSecretSocialite": score_secret_socialite,
                    "scoreStackingDubs": score_stacking_dubs,
                    "scoreLicenseToKill": score_license_to_kill,
                    "scoreAimForTheHead": score_aim_for_the_head,
                    "scorePowerTrip": score_power_trip,
                    "scoreBotBullying": score_bot_bullying,
                    "scoreOneFundo": score_one_fundo,
                    "scoreGleeFiddy": score_glee_fiddy,
                    "scoreWellTraveled": score_well_traveled,
                    "scoreMoModesMoFun": score_mo_modes_mo_fun,
                    "scoreEpidemic": score_epidemic,
                    "completedFinishInFive": completed_finish_in_five,
                    "completedVictoryLap": completed_victory_lap,
                    "completedTypeA": completed_type_a,
                    "completedFormerlyChucks": completed_formerly_chucks,
                    "completedInParticular": completed_in_particular,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
