import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.link.models import DiscordXboxLiveLink
from apps.trailblazers.serializers import (
    SeasonalRoleCheckRequestSerializer,
    SeasonalRoleCheckResponseSerializer,
)
from apps.trailblazers.utils import get_scout_qualified, get_sherpa_qualified
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
        Halo Infinite API and the HFT DB, and returning a payload indicating the seasonal Trailblazer progression role
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
                sherpa_discord_ids = get_sherpa_qualified(links)
                scout_discord_ids = get_scout_qualified(links)
            except Exception as ex:
                logger.error("Error attempting the Trailblazer seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Trailblazer seasonal role check."
                )
            serializer = SeasonalRoleCheckResponseSerializer(
                {
                    "sherpa": sherpa_discord_ids,
                    "scout": scout_discord_ids,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
