import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.exceptions import MissingEraDataException
from apps.halo_infinite.utils import get_csrs, get_current_era
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.constants import TRAILBLAZER_TITAN_CSR_MINIMUM
from apps.trailblazer.serializers import (
    TrailblazerScoutEra1ProgressResponseSerializer,
    TrailblazerScoutEra2ProgressResponseSerializer,
    TrailblazerScoutEra3ProgressResponseSerializer,
    TrailblazerScoutProgressRequestSerializer,
    TrailblazerScoutProgressResponseSerializer,
    TrailblazerTitanCheckRequestSerializer,
    TrailblazerTitanCheckResponseSerializer,
    TrailblazerTitanCheckSerializer,
)
from apps.trailblazer.utils import (
    get_e1_discord_earn_dict,
    get_e1_xbox_earn_dict,
    get_e2_discord_earn_dict,
    get_e2_xbox_earn_dict,
    get_e3_discord_earn_dict,
    get_e3_xbox_earn_dict,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


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
            import traceback

            traceback.print_exc()
            raise APIException("Error attempting the Trailblazer Scout progress check.")

        validation_serializer = TrailblazerScoutProgressRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            try:
                # Get the Era
                era = None
                try:
                    era = get_current_era()
                except MissingEraDataException:
                    pass
                assert era is not None

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
                if era == 1:
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
                elif era == 3:
                    serializer_class = TrailblazerScoutEra3ProgressResponseSerializer
                    # Tally the Discord Points
                    discord_earns = get_e3_discord_earn_dict(
                        [discord_account.discord_id]
                    ).get(discord_account.discord_id)
                    # Tally the Xbox Points
                    xbox_earns = {}
                    if link is not None:
                        xbox_earns = get_e3_xbox_earn_dict(
                            [link.xbox_live_account_id]
                        ).get(link.xbox_live_account_id)
                    serializable_dict["pointsCSRGoUp"] = xbox_earns.get("csr_go_up", 0)
                    serializable_dict["pointsBombDotCom"] = xbox_earns.get(
                        "bomb_dot_com", 0
                    )
                    serializable_dict["pointsOddlyEffective"] = xbox_earns.get(
                        "oddly_effective", 0
                    )
                    serializable_dict["pointsItsTheAge"] = xbox_earns.get(
                        "its_the_age", 0
                    )
                    serializable_dict["pointsOverkill"] = xbox_earns.get("overkill", 0)
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
