import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.link.models import DiscordXboxLiveLink
from apps.pathfinders.serializers import (
    PathfinderRoleCheckRequestSerializer,
    PathfinderRoleCheckResponseSerializer,
)
from apps.pathfinders.utils import get_dynamo_qualified, get_illuminated_qualified
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class PathfinderRoleCheckView(APIView):
    @extend_schema(
        request=PathfinderRoleCheckRequestSerializer,
        responses={
            200: PathfinderRoleCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API and the HFT DB, and returning a payload indicating the special Pathfinder Progression Role
        each Discord ID qualifies for, if any.
        """
        validation_serializer = PathfinderRoleCheckRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_ids = validation_serializer.data.get("discordUserIds")
            try:
                # Get all verified DiscordXboxLiveLink records matching the input discordUserIDs
                links = list(
                    DiscordXboxLiveLink.objects.filter(
                        discord_account_id__in=discord_ids
                    )
                    .filter(verified=True)
                    .order_by("created_at")
                )

                # Retrieve qualifying Sherpa/Scout IDs from the utility methods
                illuminated_discord_ids = get_illuminated_qualified(links)
                dynamo_discord_ids = get_dynamo_qualified(links)
            except Exception as ex:
                logger.error("Error attempting the Pathfinder role check.")
                logger.error(ex)
                raise APIException("Error attempting the Pathfinder role check.")
            serializer = PathfinderRoleCheckResponseSerializer(
                {
                    "illuminated": illuminated_discord_ids,
                    "dynamo": dynamo_discord_ids,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
