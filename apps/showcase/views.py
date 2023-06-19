import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.api.files import get_map, get_mode, get_prefab
from apps.showcase.models import ShowcaseFile
from apps.showcase.serializers import (
    CheckShowcaseRequestSerializer,
    CheckShowcaseResponseSerializer,
    ShowcaseFileDataSerializer,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class CheckShowcaseView(APIView):
    @extend_schema(
        request=CheckShowcaseRequestSerializer,
        responses={
            200: CheckShowcaseResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Retrieve a Discord Account's full Showcase data, if any exists.
        """
        validation_serializer = CheckShowcaseRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            showcase_file_data = []

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                showcase_files = ShowcaseFile.objects.filter(
                    showcase_owner=discord_account
                ).order_by("position")
                for showcase_file in showcase_files:
                    raw_api_data = {}
                    waypoint_url = ""
                    if showcase_file.file_type == ShowcaseFile.FileType.Map:
                        raw_api_data = get_map(showcase_file.file_id)
                        waypoint_url = f"https://www.halowaypoint.com/halo-infinite/ugc/maps/{showcase_file.file_id}"
                    elif showcase_file.file_type == ShowcaseFile.FileType.Mode:
                        raw_api_data = get_mode(showcase_file.file_id)
                        waypoint_url = f"https://www.halowaypoint.com/halo-infinite/ugc/modes/{showcase_file.file_id}"
                    elif showcase_file.file_type == ShowcaseFile.FileType.Prefab:
                        raw_api_data = get_prefab(showcase_file.file_id)
                        waypoint_url = f"https://www.halowaypoint.com/halo-infinite/ugc/prefabs/{showcase_file.file_id}"
                    thumbnail_url = (
                        raw_api_data.get("Files", {}).get("Prefix")
                        + list(
                            filter(
                                lambda x: "thumbnail" in x,
                                raw_api_data.get("Files", {}).get(
                                    "FileRelativePaths", []
                                ),
                            )
                        )[0]
                    )
                    showcase_file_data.append(
                        ShowcaseFileDataSerializer(
                            {
                                "fileType": showcase_file.file_type,
                                "name": raw_api_data.get("PublicName"),
                                "description": raw_api_data.get("Description"),
                                "thumbnailURL": thumbnail_url,
                                "waypointURL": waypoint_url,
                                "plays": raw_api_data.get("AssetStats", {}).get(
                                    "PlaysAllTime"
                                ),
                                "favorites": raw_api_data.get("AssetStats", {}).get(
                                    "Favorites"
                                ),
                                "ratings": raw_api_data.get("AssetStats", {}).get(
                                    "NumberOfRatings"
                                ),
                                "averageRating": raw_api_data.get("AssetStats", {}).get(
                                    "AverageRating"
                                ),
                            }
                        ).data
                    )
            except Exception as ex:
                logger.error("Error attempting to check a Showcase.")
                logger.error(ex)
                raise APIException("Error attempting to check a Showcase.")
            serializer = CheckShowcaseResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "showcaseFiles": showcase_file_data,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


# ShowcaseFileAddView

# ShowcaseFileRemoveView
