import datetime
import logging

import pytz
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import APIException, ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)
from apps.fun_time_friday.serializers import (
    PartyTimeSerializer,
    ReportSerializer,
    VoiceConnectPostRequestSerializer,
    VoiceConnectPostResponseSerializer,
    VoiceDisconnectPostRequestSerializer,
    VoiceDisconnectPostResponseSerializer,
)
from apps.fun_time_friday.utils import get_voice_connection_report
from config.serializers import StandardErrorSerializer

logger = logging.getLogger(__name__)


class ReportView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="fridayDate",
                type={"type": "string", "format": "date"},
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            )
        ],
        responses={
            200: ReportSerializer,
            400: StandardErrorSerializer,
            403: StandardErrorSerializer,
            500: StandardErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternChatter if the destination channel isn't forbidden and Intern chatter isn't paused.
        """
        # Validate that the date is in fact a Friday
        friday_date = request.query_params.get("fridayDate")
        try:
            friday = datetime.datetime.strptime(friday_date, "%Y-%m-%d").date()
            if friday.weekday() != 4:
                raise Exception("Date is not a Friday.")
        except Exception as ex:
            logger.error(ex)
            raise ParseError("Invalid 'fridayDate' provided.")

        friday_noon = pytz.timezone("America/Denver").localize(
            datetime.datetime(
                friday.year,
                friday.month,
                friday.day,
                12,
                0,
                0,
                0,
            )
        )
        saturday_noon = friday_noon + datetime.timedelta(days=1)
        report_data = get_voice_connection_report(
            time_start=friday_noon, time_end=saturday_noon
        )
        if report_data is not None:
            party_animals = []
            for animal in report_data["party_animals"]:
                party_animals.append(
                    PartyTimeSerializer(
                        {
                            "discordId": animal["discord_id"],
                            "seconds": animal["seconds"],
                        }
                    )
                )
            party_poopers = []
            for pooper in report_data["party_poopers"]:
                party_poopers.append(
                    PartyTimeSerializer(
                        {
                            "discordId": pooper["discord_id"],
                            "seconds": pooper["seconds"],
                        }
                    )
                )
            serializer = ReportSerializer(
                {
                    "totalPlayers": report_data["total_players"],
                    "totalHours": report_data["total_hours"],
                    "totalChannels": report_data["total_channels"],
                    "partyAnimals": party_animals,
                    "partyPoopers": party_poopers,
                }
            )
        else:
            serializer = ReportSerializer(
                {
                    "totalPlayers": 0,
                    "totalHours": 0,
                    "totalChannels": 0,
                    "partyAnimals": [],
                    "partyPoopers": [],
                }
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


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
