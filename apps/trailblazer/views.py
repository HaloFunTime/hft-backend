import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.exceptions import (
    MissingEraDataException,
    MissingSeasonDataException,
)
from apps.halo_infinite.utils import get_csrs, get_current_era, get_current_season_id
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.constants import TRAILBLAZER_TITAN_CSR_MINIMUM
from apps.trailblazer.serializers import (
    TrailblazerScoutEra1ProgressResponseSerializer,
    TrailblazerScoutEra2ProgressResponseSerializer,
    TrailblazerScoutProgressRequestSerializer,
    TrailblazerScoutProgressResponseSerializer,
    TrailblazerScoutSeason3ProgressResponseSerializer,
    TrailblazerScoutSeason4ProgressResponseSerializer,
    TrailblazerScoutSeason5ProgressResponseSerializer,
    TrailblazerSeasonalRoleCheckRequestSerializer,
    TrailblazerSeasonalRoleCheckResponseSerializer,
    TrailblazerTitanCheckRequestSerializer,
    TrailblazerTitanCheckResponseSerializer,
    TrailblazerTitanCheckSerializer,
)
from apps.trailblazer.utils import (
    get_e1_discord_earn_dict,
    get_e1_xbox_earn_dict,
    get_e2_discord_earn_dict,
    get_e2_xbox_earn_dict,
    get_s3_discord_earn_dict,
    get_s3_xbox_earn_dict,
    get_s4_discord_earn_dict,
    get_s4_xbox_earn_dict,
    get_s5_discord_earn_dict,
    get_s5_xbox_earn_dict,
    is_scout_qualified,
    is_sherpa_qualified,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class TrailblazerSeasonalRoleCheckView(APIView):
    @extend_schema(
        request=TrailblazerSeasonalRoleCheckRequestSerializer,
        responses={
            200: TrailblazerSeasonalRoleCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a Discord User ID by retrieving its verified linked Xbox Live gamertag, querying stats from the Halo
        Infinite API and the HFT DB, and returning a payload indicating the seasonal Trailblazer progression roles the
        Discord User ID qualifies for, if any.
        """
        validation_serializer = TrailblazerSeasonalRoleCheckRequestSerializer(
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

                sherpa_qualified = False
                scout_qualified = False
                if link is not None:
                    sherpa_qualified = is_sherpa_qualified(link.xbox_live_account_id)
                    scout_qualified = is_scout_qualified(
                        discord_account.discord_id, link.xbox_live_account_id
                    )
                else:
                    scout_qualified = is_scout_qualified(
                        discord_account.discord_id, None
                    )
            except Exception as ex:
                logger.error("Error attempting the Trailblazer seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Trailblazer seasonal role check."
                )
            serializer = TrailblazerSeasonalRoleCheckResponseSerializer(
                {
                    "discordUserId": discord_account.discord_id,
                    "sherpa": sherpa_qualified,
                    "scout": scout_qualified,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class TrailblazerScoutProgressView(APIView):
    @extend_schema(
        request=TrailblazerScoutProgressRequestSerializer,
        responses={
            200: TrailblazerScoutProgressResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate an individual Discord ID's progress toward the Trailblazer Scout role.
        """

        def raise_exception(ex):
            logger.error("Error attempting the Trailblazer Scout progress check.")
            logger.error(ex)
            raise APIException("Error attempting the Trailblazer Scout progress check.")

        validation_serializer = TrailblazerScoutProgressRequestSerializer(
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
                    serializer_class = TrailblazerScoutSeason3ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s3_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsChurchOfTheCrab"] = discord_earns.get(
                        "church_of_the_crab", 0
                    )
                    serializable_dict["pointsSharingIsCaring"] = discord_earns.get(
                        "sharing_is_caring", 0
                    )
                    serializable_dict["pointsBookworm"] = discord_earns.get(
                        "bookworm", 0
                    )
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s3_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsOnlineWarrior"] = xbox_earns.get(
                        "online_warrior", 0
                    )
                    serializable_dict["pointsHotStreak"] = xbox_earns.get(
                        "hot_streak", 0
                    )
                    serializable_dict["pointsOddlyEffective"] = xbox_earns.get(
                        "oddly_effective", 0
                    )
                    serializable_dict["pointsTooStronk"] = xbox_earns.get(
                        "too_stronk", 0
                    )
                elif season_id == "4":
                    serializer_class = TrailblazerScoutSeason4ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s4_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsChurchOfTheCrab"] = discord_earns.get(
                        "church_of_the_crab", 0
                    )
                    serializable_dict["pointsBookworm"] = discord_earns.get(
                        "bookworm", 0
                    )
                    serializable_dict["pointsFilmCritic"] = discord_earns.get(
                        "film_critic", 0
                    )
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s4_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsOnlineWarrior"] = xbox_earns.get(
                        "online_warrior", 0
                    )
                    serializable_dict["pointsTheCycle"] = xbox_earns.get("the_cycle", 0)
                    serializable_dict["pointsCheckeredFlag"] = xbox_earns.get(
                        "checkered_flag", 0
                    )
                    serializable_dict["pointsThemTharHills"] = xbox_earns.get(
                        "them_thar_hills", 0
                    )
                elif season_id == "5":
                    serializer_class = TrailblazerScoutSeason5ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_s5_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsChurchOfTheCrab"] = discord_earns.get(
                        "church_of_the_crab", 0
                    )
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_s5_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsOnlineWarrior"] = xbox_earns.get(
                        "online_warrior", 0
                    )
                    serializable_dict["pointsHeadsOrTails"] = xbox_earns.get(
                        "heads_or_tails", 0
                    )
                    serializable_dict["pointsHighVoltage"] = xbox_earns.get(
                        "high_voltage", 0
                    )
                    serializable_dict["pointsExterminator"] = xbox_earns.get(
                        "exterminator", 0
                    )
                elif era == 1:
                    serializer_class = TrailblazerScoutEra1ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_e1_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsChurchOfTheCrab"] = discord_earns.get(
                        "church_of_the_crab", 0
                    )
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_e1_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsCSRGoUp"] = xbox_earns.get("csr_go_up", 0)
                    serializable_dict["pointsPlayToSlay"] = xbox_earns.get(
                        "play_to_slay", 0
                    )
                    serializable_dict["pointsMeanStreets"] = xbox_earns.get(
                        "mean_streets", 0
                    )
                    serializable_dict["pointsHotStreak"] = xbox_earns.get(
                        "hot_streak", 0
                    )
                elif era == 2:
                    serializer_class = TrailblazerScoutEra2ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_e2_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    serializable_dict["pointsChurchOfTheCrab"] = discord_earns.get(
                        "church_of_the_crab", 0
                    )
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_e2_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsCSRGoUp"] = xbox_earns.get("csr_go_up", 0)
                    serializable_dict["pointsTooStronk"] = xbox_earns.get(
                        "too_stronk", 0
                    )
                    serializable_dict["pointsScoreboard"] = xbox_earns.get(
                        "scoreboard", 0
                    )
                    serializable_dict["pointsTheCycle"] = xbox_earns.get("the_cycle", 0)
            except Exception as ex:
                raise_exception(ex)
            merged_dict = {
                "linkedGamertag": link is not None,
                "totalPoints": sum(serializable_dict.values()),
            } | serializable_dict
            serializer = serializer_class(merged_dict)
            return Response(serializer.data, status=status.HTTP_200_OK)


class TrailblazerTitanCheckView(APIView):
    @extend_schema(
        request=TrailblazerTitanCheckRequestSerializer,
        responses={
            200: TrailblazerTitanCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API, and returning a payload indicating whether or not each one qualifies for Trailblazer Titan.
        """
        validation_serializer = TrailblazerTitanCheckRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            playlist_id = validation_serializer.data.get("playlistId")
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

                # Get CSRs for all XUIDs for the playlist ID in question
                csr_by_xuid = get_csrs(xuids, playlist_id).get("csrs")

                # For each Trailblazer XUID, add Discord IDs to the appropriate yes/no list
                linked_discord_ids = set()
                yes = []
                no = []
                for xuid_str in csr_by_xuid:
                    current_csr = csr_by_xuid[xuid_str]["current_csr"]
                    discord_id = xuid_to_discord_id.get(int(xuid_str))
                    linked_discord_ids.add(discord_id)
                    if (
                        current_csr is not None
                        and current_csr >= TRAILBLAZER_TITAN_CSR_MINIMUM
                    ):
                        yes.append(
                            TrailblazerTitanCheckSerializer(
                                {
                                    "discordUserId": discord_id,
                                    "currentCSR": current_csr,
                                }
                            ).data
                        )
                    else:
                        no.append(
                            TrailblazerTitanCheckSerializer(
                                {
                                    "discordUserId": discord_id,
                                    "currentCSR": current_csr,
                                }
                            ).data
                        )
                # For Discord IDs without linked gamertags, automatically add them to the no list
                unlinked_discord_ids = set(discord_ids).difference(linked_discord_ids)
                for discord_id in unlinked_discord_ids:
                    no.append(
                        TrailblazerTitanCheckSerializer(
                            {
                                "discordUserId": discord_id,
                                "currentCSR": None,
                            }
                        ).data
                    )
            except Exception as ex:
                logger.error("Error attempting the Trailblazer Titan check.")
                logger.error(ex)
                raise APIException("Error attempting the Trailblazer Titan check.")
            serializer = TrailblazerTitanCheckResponseSerializer(
                {
                    "yes": yes,
                    "no": no,
                    "thresholdCSR": TRAILBLAZER_TITAN_CSR_MINIMUM,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
