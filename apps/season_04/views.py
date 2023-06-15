import datetime
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
    GAME_VARIANT_CATEGORY_INFECTION,
    MEDAL_ID_PERFECTION,
    PLAYLIST_ID_BOT_BOOTCAMP,
    SEASON_3_API_ID,
    SEASON_3_DEV_MAP_IDS,
    SEASON_3_END_TIME,
    SEASON_3_START_TIME,
)
from apps.halo_infinite.utils import get_season_custom_matches_for_xuid
from apps.link.models import DiscordXboxLiveLink
from apps.reputation.models import PlusRep
from apps.season_04.models import (
    StampChallenge16Completion,
    StampChallenge17Completion,
    StampChallenge18Completion,
    StampChallenge19Completion,
    StampChallenge20Completion,
)
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
            score_one_fundo = 0
            score_glee_fiddy = 0
            score_well_traveled = 0
            score_mo_modes_mo_fun = 0
            score_epidemic = 0
            completed_finish_in_five = False
            completed_victory_lap = False
            completed_type_a = False
            completed_formerly_chucks = False
            completed_in_particular = False
            # TODO: Update the following variables for Season 4 when known
            season_start_time = SEASON_3_START_TIME
            season_end_time = SEASON_3_END_TIME
            season_api_id = SEASON_3_API_ID
            season_dev_map_ids = SEASON_3_DEV_MAP_IDS
            season_id = "3"
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

                    # HALO INFINITE CUSTOM GAME CHALLENGES
                    custom_matches = get_season_custom_matches_for_xuid(
                        link.xbox_live_account_id, season_id
                    )
                    custom_matches_sorted = sorted(
                        custom_matches,
                        key=lambda m: datetime.datetime.fromisoformat(
                            m.get("MatchInfo", {}).get("StartTime")
                        ),
                    )
                    games_finished = 0
                    seconds_played = 0
                    non_dev_maps_played = set()
                    modes_played = set()
                    infection_games_finished = 0
                    for match in custom_matches_sorted:
                        # Count finished matches
                        if match.get("PresentAtEndOfMatch", True):
                            games_finished += 1
                            if (
                                match.get("MatchInfo", {}).get("GameVariantCategory")
                                == GAME_VARIANT_CATEGORY_INFECTION
                            ):
                                infection_games_finished += 1
                        # Count time per match
                        match_start = datetime.datetime.strptime(
                            match.get("MatchInfo", {})
                            .get("StartTime", None)
                            .rstrip("Z")
                            .split(".")[0],
                            "%Y-%m-%dT%H:%M:%S",
                        ).replace(tzinfo=datetime.timezone.utc)
                        match_end = datetime.datetime.strptime(
                            match.get("MatchInfo", {})
                            .get("EndTime", None)
                            .rstrip("Z")
                            .split(".")[0],
                            "%Y-%m-%dT%H:%M:%S",
                        ).replace(tzinfo=datetime.timezone.utc)
                        seconds_played += (match_end - match_start).total_seconds()
                        # Aggregate non-dev maps played
                        map_id = (
                            match.get("MatchInfo", {})
                            .get("MapVariant", {})
                            .get("AssetId", {})
                        )
                        if map_id not in season_dev_map_ids:
                            non_dev_maps_played.add(map_id)
                        # Aggregate modes played
                        mode_id = (
                            match.get("MatchInfo", {})
                            .get("UgcGameVariant", {})
                            .get("AssetId", {})
                        )
                        modes_played.add(mode_id)
                    # CHALLENGE #11: One Fundo
                    score_one_fundo = games_finished
                    if score_one_fundo >= 100:
                        stamps_completed += 1
                    # CHALLENGE #12: Glee Fiddy
                    score_glee_fiddy = int(seconds_played / 3600)
                    if score_glee_fiddy >= 50:
                        stamps_completed += 1
                    # CHALLENGE #13: Well-Traveled
                    score_well_traveled = len(non_dev_maps_played)
                    if score_well_traveled >= 50:
                        stamps_completed += 1
                    # CHALLENGE #14: Mo' Modes Mo' Fun
                    score_mo_modes_mo_fun = len(modes_played)
                    if score_mo_modes_mo_fun >= 25:
                        stamps_completed += 1
                    # CHALLENGE #15: Epidemic
                    score_epidemic = infection_games_finished
                    if score_epidemic >= 25:
                        stamps_completed += 1

                    # HALOFUNTIME BTB CHALLENGES
                    # CHALLENGE #16: Finish in Five
                    completed_finish_in_five = (
                        StampChallenge16Completion.objects.filter(
                            xuid=link.xbox_live_account_id
                        ).count()
                        > 0
                    )
                    if completed_finish_in_five:
                        stamps_completed += 1
                    # CHALLENGE #17: Victory Lap
                    completed_victory_lap = (
                        StampChallenge17Completion.objects.filter(
                            xuid=link.xbox_live_account_id
                        ).count()
                        > 0
                    )
                    if completed_victory_lap:
                        stamps_completed += 1
                    # CHALLENGE #18: Type A
                    completed_type_a = (
                        StampChallenge18Completion.objects.filter(
                            xuid=link.xbox_live_account_id
                        ).count()
                        > 0
                    )
                    if completed_type_a:
                        stamps_completed += 1
                    # CHALLENGE #19: Formerly Chuck's
                    completed_formerly_chucks = (
                        StampChallenge19Completion.objects.filter(
                            xuid=link.xbox_live_account_id
                        ).count()
                        > 0
                    )
                    if completed_formerly_chucks:
                        stamps_completed += 1
                    # CHALLENGE #20: In Particular
                    completed_in_particular = (
                        StampChallenge20Completion.objects.filter(
                            xuid=link.xbox_live_account_id
                        ).count()
                        > 0
                    )
                    if completed_in_particular:
                        stamps_completed += 1
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
