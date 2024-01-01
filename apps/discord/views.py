import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.models import DiscordLFGThreadHelpPrompt
from apps.discord.serializers import (
    CSRSnapshot,
    CSRSnapshotRequestSerializer,
    CSRSnapshotResponseSerializer,
    LFGThreadHelpPromptRequestSerializer,
    LFGThreadHelpPromptResponseSerializer,
    RankedRoleCheckRequestSerializer,
    RankedRoleCheckResponseSerializer,
)
from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.utils import get_csrs
from apps.link.models import DiscordXboxLiveLink
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CSRSnapshotView(APIView):
    @extend_schema(
        request=CSRSnapshotRequestSerializer,
        responses={
            200: CSRSnapshotResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API, and returning a payload indicating the current CSR info for each Discord ID, if applicable.
        """
        validation_serializer = CSRSnapshotRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            playlist_id = validation_serializer.data.get("playlistId")
            try:
                # Get the XUIDs from all DiscordXboxLiveLink records matching the input discordUserIDs
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

                # For each XUID in the returned list, add Discord IDs to the appropriate tier list
                players = []
                for xuid_str in csr_by_xuid:
                    players.append(
                        CSRSnapshot(
                            {
                                "discordUserId": xuid_to_discord_id.get(int(xuid_str)),
                                "currentCSR": csr_by_xuid[xuid_str]["current_csr"],
                                "currentResetMaxCSR": csr_by_xuid[xuid_str][
                                    "current_reset_max_csr"
                                ],
                                "allTimeMaxCSR": csr_by_xuid[xuid_str][
                                    "all_time_max_csr"
                                ],
                            }
                        ).data
                    )
            except Exception as ex:
                logger.error("Error attempting the CSR snapshot.")
                logger.error(ex)
                raise APIException("Error attempting the CSR snapshot.")
            serializer = CSRSnapshotResponseSerializer({"players": players})
            return Response(serializer.data, status=status.HTTP_200_OK)


class LFGThreadHelpPromptView(APIView):
    @extend_schema(
        request=LFGThreadHelpPromptRequestSerializer,
        responses={
            200: LFGThreadHelpPromptResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Returns a boolean indicating whether or not a given Discord User has been shown the LFG Help message for the
        LFG thread they're posting in previously. Creates an LFGThreadHelpPrompt record if not.
        """
        validation_serializer = LFGThreadHelpPromptRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            lfg_thread_id = validation_serializer.data.get("lfgThreadId")
            lfg_thread_name = validation_serializer.data.get("lfgThreadName")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                new = (
                    DiscordLFGThreadHelpPrompt.objects.filter(
                        help_receiver_discord_id=discord_account.discord_id,
                        lfg_thread_id=lfg_thread_id,
                    ).count()
                    == 0
                )
                if new:
                    DiscordLFGThreadHelpPrompt.objects.create(
                        creator=request.user,
                        help_receiver_discord=discord_account,
                        lfg_thread_id=lfg_thread_id,
                        lfg_thread_name=lfg_thread_name,
                    )
            except Exception as ex:
                logger.error("Error attempting LFG Thread Help.")
                logger.error(ex)
                raise APIException("Error attempting LFG Thread Help.")
            serializer = LFGThreadHelpPromptResponseSerializer(
                {"success": True, "new": new}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class RankedRoleCheckView(APIView):
    @extend_schema(
        request=RankedRoleCheckRequestSerializer,
        responses={
            200: RankedRoleCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API, and returning a payload indicating the rank Tier each Discord ID belongs to, if applicable.
        """
        validation_serializer = RankedRoleCheckRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            playlist_id = validation_serializer.data.get("playlistId")
            try:
                # Get the XUIDs from all DiscordXboxLiveLink records matching the input discordUserIDs
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

                # For each XUID in the returned list, add Discord IDs to the appropriate tier list
                onyx = []
                diamond = []
                platinum = []
                gold = []
                silver = []
                bronze = []
                unranked = []
                for xuid_str in csr_by_xuid:
                    tier = csr_by_xuid[xuid_str]["current_reset_max_tier"]
                    discord_id = xuid_to_discord_id.get(int(xuid_str))
                    if tier == "Onyx":
                        onyx.append(discord_id)
                    elif tier == "Diamond":
                        diamond.append(discord_id)
                    elif tier == "Platinum":
                        platinum.append(discord_id)
                    elif tier == "Gold":
                        gold.append(discord_id)
                    elif tier == "Silver":
                        silver.append(discord_id)
                    elif tier == "Bronze":
                        bronze.append(discord_id)
                    else:
                        unranked.append(discord_id)
            except Exception as ex:
                logger.error("Error attempting the ranked role check.")
                logger.error(ex)
                raise APIException("Error attempting the ranked role check.")
            serializer = RankedRoleCheckResponseSerializer(
                {
                    "onyx": onyx,
                    "diamond": diamond,
                    "platinum": platinum,
                    "gold": gold,
                    "silver": silver,
                    "bronze": bronze,
                    "unranked": unranked,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
