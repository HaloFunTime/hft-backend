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
    CareerRankResponseSerializer,
    CSRDataSerializer,
    CSRPlaylistSerializer,
    CSRResponseSerializer,
    RecentGameSerializer,
    RecentGamesResponseSerializer,
    SummaryCustomSerializer,
    SummaryLocalSerializer,
    SummaryMatchmakingSerializer,
    SummaryStatsResponseSerializer,
    UpdateActivePlaylistMapModePairsRequestSerializer,
    UpdateActivePlaylistMapModePairsResponseSerializer,
)
from apps.halo_infinite.utils import (
    get_career_ranks,
    get_csrs,
    get_recent_games,
    get_summary_stats,
    update_active_playlists,
    update_map_mode_pairs_for_playlists,
)
from apps.xbox_live.utils import get_xuid_and_exact_gamertag
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)

ERROR_GAMERTAG_MISSING = "Missing 'gamertag' query parameter."
ERROR_GAMERTAG_INVALID = "The gamertag you specified has invalid characters."
ERROR_GAMERTAG_NOT_FOUND = "The gamertag you specified was not found on Xbox Live."
ERROR_MATCH_TYPE_MISSING = "Missing 'matchType' query parameter."
ERROR_MATCH_TYPE_INVALID = "The match type you specified is invalid. Valid match types are 'Custom' and 'Matchmaking'."


class CareerRankView(APIView):
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
            200: CareerRankResponseSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            404: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the current Career Rank for a given gamertag.
        """
        # Validate that there is a passed-in gamertag
        gamertag_param = request.query_params.get("gamertag")
        if gamertag_param is None:
            raise ParseError(detail=ERROR_GAMERTAG_MISSING)
        gamertag = gamertag_param.replace("#", "", 1)
        if not re.match(r"[ a-zA-Z][ a-zA-Z0-9]{0,14}", gamertag):
            raise ParseError(detail=ERROR_GAMERTAG_INVALID)

        logger.debug(f"Called Career Rank endpoint with gamertag '{gamertag}'")
        gamertag_info = get_xuid_and_exact_gamertag(gamertag)
        xuid = gamertag_info[0]
        gamertag = gamertag_info[1]
        if xuid is None or gamertag is None:
            raise NotFound(ERROR_GAMERTAG_NOT_FOUND)

        try:
            career_rank_data = get_career_ranks([xuid])
            xuid_career_rank_data = career_rank_data.get("career_ranks").get(xuid)
        except Exception as ex:
            logger.error(ex)
            raise APIException(f"Could not get Career Rank for gamertag {gamertag}.")

        serializer = CareerRankResponseSerializer(
            {
                "gamertag": gamertag,
                "xuid": xuid,
                "currentRankNumber": xuid_career_rank_data["current_rank_number"],
                "currentRankName": xuid_career_rank_data["current_rank_name"],
                "currentRankScore": xuid_career_rank_data["current_rank_score"],
                "currentRankScoreMax": xuid_career_rank_data["current_rank_score_max"],
                "cumulativeScore": xuid_career_rank_data["cumulative_score"],
                "cumulativeScoreMax": xuid_career_rank_data["cumulative_score_max"],
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


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
                xuid_csr_data = csr_data.get("csrs", {}).get(xuid, {})
                playlists.append(
                    CSRPlaylistSerializer(
                        {
                            "playlistId": playlist.playlist_id,
                            "playlistName": playlist.name,
                            "playlistDescription": playlist.description,
                            "current": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("current_csr"),
                                    "tier": xuid_csr_data.get("current_tier"),
                                    "subtier": xuid_csr_data.get("current_subtier"),
                                    "tierDescription": xuid_csr_data.get(
                                        "current_tier_description"
                                    ),
                                }
                            ).data,
                            "currentResetMax": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("current_reset_max_csr"),
                                    "tier": xuid_csr_data.get("current_reset_max_tier"),
                                    "subtier": xuid_csr_data.get(
                                        "current_reset_max_subtier"
                                    ),
                                    "tierDescription": xuid_csr_data.get(
                                        "current_reset_max_tier_description"
                                    ),
                                }
                            ).data,
                            "allTimeMax": CSRDataSerializer(
                                {
                                    "csr": xuid_csr_data.get("all_time_max_csr"),
                                    "tier": xuid_csr_data.get("all_time_max_tier"),
                                    "subtier": xuid_csr_data.get(
                                        "all_time_max_subtier"
                                    ),
                                    "tierDescription": xuid_csr_data.get(
                                        "all_time_max_tier_description"
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


class RecentGamesView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="gamertag",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            ),
            OpenApiParameter(
                name="matchType",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            ),
        ],
        responses={
            200: RecentGamesResponseSerializer,
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
        # Validate that there is a passed-in type
        match_type_param = request.query_params.get("matchType")
        if match_type_param is None:
            raise ParseError(detail=ERROR_MATCH_TYPE_MISSING)
        match_type = match_type_param.title()
        if (
            match_type_param != "Custom"
            and match_type_param != "Matchmaking"
            and match_type_param != "Local"
        ):
            raise ParseError(detail=ERROR_MATCH_TYPE_INVALID)

        gamertag_info = get_xuid_and_exact_gamertag(gamertag)
        xuid = gamertag_info[0]
        gamertag = gamertag_info[1]
        if xuid is None or gamertag is None:
            raise NotFound(ERROR_GAMERTAG_NOT_FOUND)
        try:
            games = get_recent_games(xuid, match_type)
        except Exception as ex:
            logger.error(ex)
            raise APIException(f"Could not get summary stats for gamertag {gamertag}.")

        serialized_games = []
        for game in games:
            serialized_games.append(
                RecentGameSerializer(
                    {
                        "matchId": game.get("match_id"),
                        "outcome": game.get("outcome"),
                        "finished": game.get("finished"),
                        "modeName": game.get("mode_name"),
                        "modeAssetId": game.get("mode_asset_id"),
                        "modeVersionId": game.get("mode_version_id"),
                        "mapName": game.get("map_name"),
                        "mapAssetId": game.get("map_asset_id"),
                        "mapVersionId": game.get("map_version_id"),
                        "mapThumbnailURL": game.get("map_thumbnail_url"),
                        "playlistName": game.get("playlist_name"),
                        "playlistAssetId": game.get("playlist_asset_id"),
                        "playlistVersionId": game.get("playlist_version_id"),
                    }
                ).data
            )

        serializer = RecentGamesResponseSerializer({"games": serialized_games})
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
            matchmaking_data = summary_data.get("matchmaking")
            custom_data = summary_data.get("custom")
            local_data = summary_data.get("local")
        except Exception as ex:
            logger.error(ex)
            raise APIException(f"Could not get summary stats for gamertag {gamertag}.")

        serializer = SummaryStatsResponseSerializer(
            {
                "gamertag": gamertag,
                "xuid": xuid,
                "matchmaking": SummaryMatchmakingSerializer(
                    {
                        "gamesPlayed": matchmaking_data.get("games_played"),
                        "wins": matchmaking_data.get("wins"),
                        "losses": matchmaking_data.get("losses"),
                        "ties": matchmaking_data.get("ties"),
                        "kills": matchmaking_data.get("kills"),
                        "deaths": matchmaking_data.get("deaths"),
                        "assists": matchmaking_data.get("assists"),
                        "kda": matchmaking_data.get("kda"),
                    }
                ).data,
                "custom": SummaryCustomSerializer(
                    {"gamesPlayed": custom_data.get("games_played")}
                ).data,
                "local": SummaryLocalSerializer(
                    {"gamesPlayed": local_data.get("games_played")}
                ).data,
                "gamesPlayed": summary_data.get("games_played"),
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateActivePlaylistMapModePairsView(APIView):
    @extend_schema(
        request=UpdateActivePlaylistMapModePairsRequestSerializer,
        responses={
            200: UpdateActivePlaylistMapModePairsResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Re-fetch all active HaloInfinitePlaylists and save HaloInfiniteMaps for each one.
        """
        validation_serializer = UpdateActivePlaylistMapModePairsRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            try:
                # Update all active Playlists
                updated_active_playlists = update_active_playlists()

                # Update all active Playlists' MapModePairs
                updated_map_mode_pairs = update_map_mode_pairs_for_playlists(
                    updated_active_playlists, request.user
                )

                logger.info(f"Updated {len(updated_map_mode_pairs)} map/mode pairs.")

            except Exception as ex:
                logger.error(
                    "Error attempting to update map/mode pairs for active playlists."
                )
                logger.error(ex)
                raise APIException(
                    "Error attempting to update map/mode pairs for active playlists."
                )
            serializer = UpdateActivePlaylistMapModePairsResponseSerializer(
                {"success": True}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
