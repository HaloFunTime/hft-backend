import logging
import re

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, NotFound, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.halo_infinite.serializers import (
    CSRDataSerializer,
    CSRPlaylistSerializer,
    CSRResponseSerializer,
    SummaryCustomSerializer,
    SummaryLocalSerializer,
    SummaryMatchmakingSerializer,
    SummaryStatsResponseSerializer,
)
from apps.halo_infinite.utils import get_csrs, get_summary_stats
from apps.xbox_live.utils import get_xuid_and_exact_gamertag
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)

ERROR_GAMERTAG_MISSING = "Missing 'gamertag' query parameter."
ERROR_GAMERTAG_INVALID = (
    "Only characters constituting a valid Xbox Live Gamertag are allowed."
)
ERROR_GAMERTAG_NOT_FOUND = "Gamertag not found on Xbox Live."


class CSRView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="gamertag",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            )
        ],
        responses={
            200: CSRResponseSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            404: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the current CSR in all active Ranked playlists for a given gamertag.
        """
        # Validate that there is a passed-in gamertag
        gamertag_param = request.query_params.get("gamertag")
        if gamertag_param is None:
            raise ParseError(detail=ERROR_GAMERTAG_MISSING)
        gamertag = gamertag_param.replace("#", "", 1)
        if not re.match(r"[ a-zA-Z][ a-zA-Z0-9]{0,14}", gamertag):
            raise ParseError(detail=ERROR_GAMERTAG_INVALID)

        logger.debug(f"Called CSR endpoint with gamertag '{gamertag}'")
        gamertag_info = get_xuid_and_exact_gamertag(gamertag)
        xuid = gamertag_info[0]
        gamertag = gamertag_info[1]
        if xuid is None or gamertag is None:
            raise NotFound(ERROR_GAMERTAG_NOT_FOUND)

        current_ranked_playlists = HaloInfinitePlaylist.objects.filter(
            ranked=True, active=True
        ).order_by("name")
        playlists = []
        try:
            for playlist in current_ranked_playlists:
                csr_data = get_csrs([xuid], playlist.playlist_id)
                xuid_csr_data = csr_data.get("csrs").get(xuid)
                playlists.append(
                    CSRPlaylistSerializer(
                        {
                            "playlist_id": playlist.playlist_id,
                            "playlist_name": playlist.name,
                            "playlist_description": playlist.description,
                            "current": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("current_csr"),
                                    "tier": xuid_csr_data.get("current_tier"),
                                    "subtier": xuid_csr_data.get("current_subtier"),
                                }
                            ).data,
                            "current_reset_max": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("current_reset_max_csr"),
                                    "tier": xuid_csr_data.get("current_reset_max_tier"),
                                    "subtier": xuid_csr_data.get(
                                        "current_reset_max_subtier"
                                    ),
                                }
                            ).data,
                            "all_time_max": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("all_time_max_csr"),
                                    "tier": xuid_csr_data.get("all_time_max_tier"),
                                    "subtier": xuid_csr_data.get(
                                        "all_time_max_subtier"
                                    ),
                                }
                            ).data,
                        }
                    ).data
                )
        except Exception as ex:
            logger.error(ex)
            raise APIException(f"Could not get CSR for gamertag {gamertag}.")

        serializer = CSRResponseSerializer(
            {
                "gamertag": gamertag,
                "xuid": xuid,
                "playlists": playlists,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class SummaryStatsView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="gamertag",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            )
        ],
        responses={
            200: SummaryStatsResponseSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            404: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the summary stats for a given gamertag.
        """
        # Validate that there is a passed-in gamertag
        gamertag_param = request.query_params.get("gamertag")
        if gamertag_param is None:
            raise ParseError(detail=ERROR_GAMERTAG_MISSING)
        gamertag = gamertag_param.replace("#", "", 1)
        if not re.match(r"[ a-zA-Z][ a-zA-Z0-9]{0,14}", gamertag):
            raise ParseError(detail=ERROR_GAMERTAG_INVALID)

        logger.debug(f"Called SummaryStats endpoint with gamertag '{gamertag}'")
        gamertag_info = get_xuid_and_exact_gamertag(gamertag)
        xuid = gamertag_info[0]
        gamertag = gamertag_info[1]
        if xuid is None or gamertag is None:
            raise NotFound(ERROR_GAMERTAG_NOT_FOUND)
        try:
            summary_data = get_summary_stats(xuid)
        except Exception as ex:
            logger.error(ex)
            raise APIException(f"Could not get summary stats for gamertag {gamertag}.")

        serializer = SummaryStatsResponseSerializer(
            {
                "gamertag": gamertag,
                "xuid": xuid,
                "matchmaking": SummaryMatchmakingSerializer(
                    summary_data.get("matchmaking")
                ).data,
                "custom": SummaryCustomSerializer(summary_data.get("custom")).data,
                "local": SummaryLocalSerializer(summary_data.get("local")).data,
                "games_played": summary_data.get("games_played"),
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
