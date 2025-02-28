import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import (
    get_or_create_discord_account,
    update_or_create_discord_account,
)
from apps.link.models import DiscordXboxLiveLink
from apps.link.serializers import (
    DiscordToXboxLiveRequestSerializer,
    DiscordXboxLiveLinkErrorSerializer,
    DiscordXboxLiveLinkResponseSerializer,
)
from apps.link.utils import (
    auto_verify_discord_xbox_live_link,
    update_or_create_discord_xbox_live_link,
)
from apps.xbox_live.utils import (
    get_gamertag_from_xuid,
    update_or_create_xbox_live_account,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)

LINK_ERROR_INVALID_DISCORD_ID = (
    "The provided discordId must be a string representing a valid positive integer."
)
LINK_ERROR_INVALID_DISCORD_USERNAME = (
    "The provided discordUsername must be a valid Discord username."
)
LINK_ERROR_MISSING_DISCORD_ID = "A discordId must be provided as a query parameter."
LINK_ERROR_MISSING_DISCORD_USERNAME = (
    "A discordUsername must be provided as a query parameter."
)
LINK_ERROR_NOT_FOUND = "Not found."


class DiscordToXboxLive(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="discordId",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            ),
            OpenApiParameter(
                name="discordUsername",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            ),
        ],
        responses={
            200: DiscordXboxLiveLinkResponseSerializer,
            400: DiscordXboxLiveLinkErrorSerializer,
            404: DiscordXboxLiveLinkErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves DiscordXboxLiveLink data for a given Discord Account.
        """
        # Validate that there is a passed-in Discord Account ID
        discord_account_id = request.query_params.get("discordId")
        if discord_account_id is None:
            serializer = DiscordXboxLiveLinkErrorSerializer(
                {"error": LINK_ERROR_MISSING_DISCORD_ID}
            )
            return Response(serializer.data, status=400)

        # Validate that the string passed in as a channel ID is numeric
        if not str(discord_account_id).isnumeric():
            serializer = DiscordXboxLiveLinkErrorSerializer(
                {"error": LINK_ERROR_INVALID_DISCORD_ID}
            )
            return Response(serializer.data, status=400)

        # Validate that there is a passed-in Discord Account Username
        discord_account_username = request.query_params.get("discordUsername")
        if discord_account_username is None:
            serializer = DiscordXboxLiveLinkErrorSerializer(
                {"error": LINK_ERROR_MISSING_DISCORD_USERNAME}
            )
            return Response(serializer.data, status=400)

        # Validate that the string passed in as a Discord Account Username meets the requirements
        if len(discord_account_username) < 2 or len(discord_account_username) > 32:
            serializer = DiscordXboxLiveLinkErrorSerializer(
                {"error": LINK_ERROR_INVALID_DISCORD_USERNAME}
            )
            return Response(serializer.data, status=400)

        # Get the DiscordAccount
        discord_account = get_or_create_discord_account(
            discord_account_id,
            request.user,
            discord_account_username,
        )

        # Get the DiscordXboxLiveLink record for the DiscordAccount, if it exists
        discord_xbox_live_link = DiscordXboxLiveLink.objects.filter(
            discord_account=discord_account
        ).first()
        if discord_xbox_live_link is None:
            serializer = DiscordXboxLiveLinkErrorSerializer(
                {"error": LINK_ERROR_NOT_FOUND}
            )
            return Response(serializer.data, status=404)

        # Update the gamertag for the XboxLiveAccount, in case it has changed
        if (
            get_gamertag_from_xuid(discord_xbox_live_link.xbox_live_account.xuid)
            != discord_xbox_live_link.xbox_live_account.gamertag
        ):
            # Re-saving the XboxLiveAccount automatically updates the gamertag
            discord_xbox_live_link.xbox_live_account.save()

        serializer = DiscordXboxLiveLinkResponseSerializer(
            {
                "discordUserId": discord_xbox_live_link.discord_account.discord_id,
                "discordUsername": discord_xbox_live_link.discord_account.discord_username,
                "xboxLiveXuid": discord_xbox_live_link.xbox_live_account.xuid,
                "xboxLiveGamertag": discord_xbox_live_link.xbox_live_account.gamertag,
                "verified": discord_xbox_live_link.verified,
            }
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=DiscordToXboxLiveRequestSerializer,
        responses={
            200: DiscordXboxLiveLinkResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Create a DiscordXboxLiveLink record from the provided information, which should uniquely identify both a Discord
        Account and an Xbox Live Account. If either or both records to link do not exist, this method will create them.
        By default, this method will attempt auto-verification of the link record by the system.
        """
        validation_serializer = DiscordToXboxLiveRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_username = validation_serializer.data.get("discordUsername")
            xbox_live_gamertag = validation_serializer.data.get("xboxLiveGamertag")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_username, request.user
                )
                xbox_live_account = update_or_create_xbox_live_account(
                    xbox_live_gamertag, request.user
                )
                discord_xbox_live_link = update_or_create_discord_xbox_live_link(
                    discord_account, xbox_live_account, request.user
                )
                # Attempt auto-verification if the link is not verified on creation
                if not discord_xbox_live_link.verified:
                    discord_xbox_live_link = auto_verify_discord_xbox_live_link(
                        discord_xbox_live_link, request.user
                    )
            except Exception as ex:
                logger.error(
                    f"Error attempting to link Discord ID {discord_id} to Xbox Live Gamertag {xbox_live_gamertag}"
                )
                logger.error(ex)
                raise APIException()
            serializer = DiscordXboxLiveLinkResponseSerializer(
                {
                    "discordUserId": discord_xbox_live_link.discord_account.discord_id,
                    "discordUsername": discord_xbox_live_link.discord_account.discord_username,
                    "xboxLiveXuid": discord_xbox_live_link.xbox_live_account.xuid,
                    "xboxLiveGamertag": discord_xbox_live_link.xbox_live_account.gamertag,
                    "verified": discord_xbox_live_link.verified,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
