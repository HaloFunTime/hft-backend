import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.halo_infinite.api.files import get_map, get_mode, get_prefab
from apps.link.models import DiscordXboxLiveLink
from apps.showcase.models import ShowcaseFile
from apps.showcase.serializers import (
    AddFileRequestSerializer,
    AddFileResponseSerializer,
    CheckShowcaseRequestSerializer,
    CheckShowcaseResponseSerializer,
    RemoveFileRequestSerializer,
    RemoveFileResponseSerializer,
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


class AddFileView(APIView):
    @extend_schema(
        request=AddFileRequestSerializer,
        responses={
            200: AddFileResponseSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Add a file to someone's Showcase (if they have room and the file meets the conditions).
        """
        validation_serializer = AddFileRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            file_type = validation_serializer.data.get("fileType")
            file_id = validation_serializer.data.get("fileId")

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                showcase_files = ShowcaseFile.objects.filter(
                    showcase_owner=discord_account
                ).order_by("position")
            except Exception as ex:
                logger.error("Error attempting to add to a Showcase.")
                logger.error(ex)
                raise APIException("Error attempting to add to a Showcase.")

            # Check linked gamertag
            link = None
            try:
                link = DiscordXboxLiveLink.objects.filter(
                    discord_account_id=discord_account.discord_id, verified=True
                ).get()
            except DiscordXboxLiveLink.DoesNotExist:
                raise PermissionDenied(
                    "Must have a verified linked gamertag to add to a Showcase."
                )

            # Check count
            if len(showcase_files) >= 5:
                raise PermissionDenied("Showcase already has 5 files.")

            try:
                file_data = None
                if file_type == "map":
                    file_data = get_map(file_id)
                elif file_type == "mode":
                    file_data = get_mode(file_id)
                elif file_type == "prefab":
                    file_data = get_prefab(file_id)
            except Exception as ex:
                logger.error("Error attempting to add to a Showcase.")
                logger.error(ex)
                raise APIException("Error attempting to add to a Showcase.")

            # Check file data
            if not file_data:
                raise PermissionDenied(
                    f"Cannot find a Halo Infinite {file_type} file with the specified ID."
                )

            # Check contributors
            contributor_xuid_strings = set()
            admin_xuid_string = file_data.get("Admin")
            if admin_xuid_string is not None:
                contributor_xuid_strings.add(admin_xuid_string)
            for contributor in file_data.get("Contributors", []):
                contributor_xuid_strings.add(contributor)
            contributor_xuids = set()
            for contributor_xuid_string in contributor_xuid_strings:
                contributor_xuids.add(
                    int(contributor_xuid_string.lstrip("xuid(").rstrip(")"))
                )
            if link.xbox_live_account_id not in contributor_xuids:
                raise PermissionDenied(
                    "Submitter must be a contributor to add to a Showcase."
                )

            # Check against existing ShowcaseFiles
            for showcase_file in showcase_files:
                if str(showcase_file.file_id) == str(file_id):
                    raise PermissionDenied("File already in Showcase.")
            try:
                # Create the ShowcaseFile
                ShowcaseFile.objects.create(
                    showcase_owner=discord_account,
                    file_type=file_type,
                    file_id=file_id,
                    position=len(showcase_files) + 1,
                    creator=request.user,
                )
            except Exception as ex:
                logger.error("Error attempting to add to a Showcase.")
                logger.error(ex)
                raise APIException("Error attempting to add to a Showcase.")
            serializer = AddFileResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "success": True,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)


class RemoveFileView(APIView):
    @extend_schema(
        request=RemoveFileRequestSerializer,
        responses={
            200: RemoveFileResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Remove a file from someone's Showcase.
        """
        validation_serializer = RemoveFileRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            position = validation_serializer.data.get("position")

            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )

                # Delete the requested ShowcaseFile
                showcase_file_to_delete = ShowcaseFile.objects.get(
                    showcase_owner=discord_account,
                    position=position,
                )
                showcase_file_to_delete.delete()

                # Move all later ShowcaseFiles forward one position
                for i in range(position + 1, 6):
                    try:
                        showcase_file = ShowcaseFile.objects.get(
                            showcase_owner=discord_account, position=i
                        )
                        showcase_file.position = showcase_file.position - 1
                        showcase_file.save()
                    except ShowcaseFile.DoesNotExist:
                        pass
            except Exception as ex:
                logger.error("Error attempting to remove from a Showcase.")
                logger.error(ex)
                raise APIException("Error attempting to remove from a Showcase.")
            serializer = RemoveFileResponseSerializer(
                {
                    "discordUserId": discord_id,
                    "success": True,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
