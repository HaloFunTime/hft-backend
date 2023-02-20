from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.link.serializers import (
    DiscordXboxLiveLinkSerializer,
    LinkDiscordAndXboxLiveErrorSerializer,
    LinkDiscordAndXboxLiveSerializer,
)
from apps.xbox_live.utils import update_or_create_xbox_live_account


class LinkDiscordAndXboxLive(APIView):
    @extend_schema(
        request=LinkDiscordAndXboxLiveSerializer,
        responses={
            200: DiscordXboxLiveLinkSerializer,
            400: LinkDiscordAndXboxLiveErrorSerializer,
            500: LinkDiscordAndXboxLiveErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Create a DiscordXboxLiveLink record from the provided information, which should uniquely identify both a Discord
        Account and an Xbox Live Account. If either or both records to link do not exist, this method will create them.
        """
        validation_serializer = LinkDiscordAndXboxLiveSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            discord_account = update_or_create_discord_account(
                validation_serializer.data.get("discordUserId"),
                validation_serializer.data.get("discordUserTag"),
            )
            xbox_live_account = update_or_create_xbox_live_account(
                validation_serializer.data.get("xboxLiveGamertag")
            )
            serializer = DiscordXboxLiveLinkSerializer(
                data={
                    "discord_account": discord_account,
                    "xbox_live_account": xbox_live_account,
                }
            )
            if serializer.is_valid(raise_exception=True):
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
