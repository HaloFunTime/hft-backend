import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)
from apps.fun_time_friday.serializers import (
    VoiceConnectPostRequestSerializer,
    VoiceConnectPostResponseSerializer,
    VoiceDisconnectPostRequestSerializer,
    VoiceDisconnectPostResponseSerializer,
)
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class VoiceConnectView(APIView):
    @extend_schema(
        request=VoiceConnectPostRequestSerializer,
        responses={
            200: VoiceConnectPostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Record that someone has connected to an FTF voice channel.
        """
        validation_serializer = VoiceConnectPostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            connector_discord_id = validation_serializer.data.get("connectorDiscordId")
            connector_discord_username = validation_serializer.data.get(
                "connectorDiscordUsername"
            )
            connected_at = validation_serializer.data.get("connectedAt")
            channel_id = validation_serializer.data.get("channelId")
            channel_name = validation_serializer.data.get("channelName") or ""
            try:
                connector_discord = update_or_create_discord_account(
                    connector_discord_id, connector_discord_username, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to record a FunTimeFridayVoiceConnect."
                )
            try:
                FunTimeFridayVoiceConnect.objects.create(
                    creator=request.user,
                    connector_discord=connector_discord,
                    connected_at=connected_at,
                    channel_id=channel_id,
                    channel_name=channel_name[:50],
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a FunTimeFridayVoiceConnect."
                )
            serializer = VoiceConnectPostResponseSerializer({"success": True})
            return Response(serializer.data, status=status.HTTP_200_OK)


class VoiceDisconnectView(APIView):
    @extend_schema(
        request=VoiceDisconnectPostRequestSerializer,
        responses={
            200: VoiceDisconnectPostResponseSerializer,
            400: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def post(self, request, format=None):
        """
        Record that someone has connected to an FTF voice channel.
        """
        validation_serializer = VoiceDisconnectPostRequestSerializer(data=request.data)
        if validation_serializer.is_valid(raise_exception=True):
            disconnector_discord_id = validation_serializer.data.get(
                "disconnectorDiscordId"
            )
            disconnector_discord_username = validation_serializer.data.get(
                "disconnectorDiscordUsername"
            )
            disconnected_at = validation_serializer.data.get("disconnectedAt")
            channel_id = validation_serializer.data.get("channelId")
            channel_name = validation_serializer.data.get("channelName") or ""
            try:
                disconnector_discord = update_or_create_discord_account(
                    disconnector_discord_id, disconnector_discord_username, request.user
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to record a FunTimeFridayVoiceDisconnect."
                )
            try:
                FunTimeFridayVoiceDisconnect.objects.create(
                    creator=request.user,
                    disconnector_discord=disconnector_discord,
                    disconnected_at=disconnected_at,
                    channel_id=channel_id,
                    channel_name=channel_name[:50],
                )
            except Exception as ex:
                logger.error(ex)
                raise APIException(
                    "Error attempting to create a FunTimeFridayVoiceDisconnect."
                )
            serializer = VoiceDisconnectPostResponseSerializer({"success": True})
            return Response(serializer.data, status=status.HTTP_200_OK)
