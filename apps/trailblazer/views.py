import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.serializers import (
    TrailblazerScoutProgressRequestSerializer,
    TrailblazerScoutProgressResponseSerializer,
    TrailblazerSeasonalRoleCheckRequestSerializer,
    TrailblazerSeasonalRoleCheckResponseSerializer,
)
from apps.trailblazer.utils import (
    get_discord_earn_dict,
    get_scout_qualified,
    get_sherpa_qualified,
    get_xbox_earn_sets,
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
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API and the HFT DB, and returning a payload indicating the seasonal Trailblazer progression role
        each Discord ID qualifies for, if any.
        """
        validation_serializer = TrailblazerSeasonalRoleCheckRequestSerializer(
            data=request.data
        )
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
                scout_discord_ids = get_scout_qualified(discord_ids, links)
            except Exception as ex:
                logger.error("Error attempting the Trailblazer seasonal role check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Trailblazer seasonal role check."
                )
            serializer = TrailblazerSeasonalRoleCheckResponseSerializer(
                {
                    "sherpa": sherpa_discord_ids,
                    "scout": scout_discord_ids,
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
        Evaluate a list of Discord IDs by retrieving their verified linked Xbox Live gamertags, querying stats from the
        Halo Infinite API and the HFT DB, and returning a payload indicating the seasonal Trailblazer progression role
        each Discord ID qualifies for, if any.
        """
        validation_serializer = TrailblazerScoutProgressRequestSerializer(
            data=request.data
        )
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            points_church_of_the_crab = 0
            points_sharing_is_caring = 0
            points_bookworm = 0
            points_online_warrior = 0
            points_hot_streak = 0
            points_oddly_effective = 0
            points_too_stronk = 0
            try:
                # Tally the Discord Points
                discord_earns = get_discord_earn_dict([discord_id]).get(discord_id)
                points_church_of_the_crab = discord_earns.get("church_of_the_crab") * 50
                points_sharing_is_caring = discord_earns.get("sharing_is_caring") * 50
                points_bookworm = discord_earns.get("bookworm") * 50

                # Tally the Xbox Points
                link = None
                try:
                    link = DiscordXboxLiveLink.objects.filter(
                        discord_account_id=discord_id, verified=True
                    ).get()
                    (
                        earned_online_warrior,
                        earned_hot_streak,
                        earned_oddly_effective,
                        earned_too_stronk,
                    ) = get_xbox_earn_sets([link.xbox_live_account_id])
                    points_online_warrior = (
                        200 if link.xbox_live_account_id in earned_online_warrior else 0
                    )
                    points_hot_streak = (
                        100 if link.xbox_live_account_id in earned_hot_streak else 0
                    )
                    points_oddly_effective = (
                        100
                        if link.xbox_live_account_id in earned_oddly_effective
                        else 0
                    )
                    points_too_stronk = (
                        100 if link.xbox_live_account_id in earned_too_stronk else 0
                    )
                except DiscordXboxLiveLink.DoesNotExist:
                    pass

                # Calculate the total points
                total_points = (
                    points_church_of_the_crab
                    + points_sharing_is_caring
                    + points_bookworm
                    + points_online_warrior
                    + points_hot_streak
                    + points_oddly_effective
                    + points_too_stronk
                )
            except Exception as ex:
                logger.error("Error attempting the Trailblazer Scout progress check.")
                logger.error(ex)
                raise APIException(
                    "Error attempting the Trailblazer Scout progress check."
                )
            serializer = TrailblazerScoutProgressResponseSerializer(
                {
                    "linkedGamertag": link is not None,
                    "totalPoints": total_points,
                    "pointsChurchOfTheCrab": points_church_of_the_crab,
                    "pointsSharingIsCaring": points_sharing_is_caring,
                    "pointsBookworm": points_bookworm,
                    "pointsOnlineWarrior": points_online_warrior,
                    "pointsHotStreak": points_hot_streak,
                    "pointsOddlyEffective": points_oddly_effective,
                    "pointsTooStronk": points_too_stronk,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
