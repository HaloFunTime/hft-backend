import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.serializers import (
    SeasonalRoleCheckRequestSerializer,
    SeasonalRoleCheckResponseSerializer,
)
from apps.pathfinder.utils import get_dynamo_qualified, get_illuminated_qualified
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class SeasonalRoleCheckView(APIView):
    @extend_schema(
        request=SeasonalRoleCheckRequestSerializer,
        responses={
            200: SeasonalRoleCheckResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API and the HFT DB, and returning a payload indicating the seasonal Pathfinder progression role
        each Discord ID qualifies for, if any.
        """
        validation_serializer = SeasonalRoleCheckRequestSerializer(data=request.data)
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
                logger.error("Error attempting the Pathfinder seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Pathfinder seasonal role check."
                )
            serializer = SeasonalRoleCheckResponseSerializer(
                {
                    "illuminated": illuminated_discord_ids,
                    "dynamo": dynamo_discord_ids,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)