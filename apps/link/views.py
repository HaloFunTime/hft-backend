import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.link.serializers import (
    DiscordXboxLiveLinkResponseSerializer,
    LinkDiscordToXboxLiveSerializer,
)
from apps.link.utils import update_or_create_discord_xbox_live_link
from apps.xbox_live.utils import update_or_create_xbox_live_account
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class LinkDiscordToXboxLive(APIView):
    @extend_schema(
        request=LinkDiscordToXboxLiveSerializer,
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
        """
        validation_serializer = LinkDiscordToXboxLiveSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_id = validation_serializer.data.get("discordUserId")
            discord_tag = validation_serializer.data.get("discordUserTag")
            xbox_live_gamertag = validation_serializer.data.get("xboxLiveGamertag")
            try:
                discord_account = update_or_create_discord_account(
                    discord_id, discord_tag, request.user
                )
                xbox_live_account = update_or_create_xbox_live_account(
                    xbox_live_gamertag, request.user
                )
                discord_xbox_live_link = update_or_create_discord_xbox_live_link(
                    discord_account, xbox_live_account, request.user
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
                    "discordUserTag": discord_xbox_live_link.discord_account.discord_tag,
                    "xboxLiveXuid": discord_xbox_live_link.xbox_live_account.xuid,
                    "xboxLiveGamertag": discord_xbox_live_link.xbox_live_account.gamertag,
                    "verified": discord_xbox_live_link.verified,
                }
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
