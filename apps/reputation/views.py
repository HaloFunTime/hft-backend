import logging

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.reputation.serializers import (
    PlusRepErrorSerializer,
    PlusRepRequestSerializer,
    PlusRepResponseSerializer,
)
from apps.reputation.utils import create_new_plus_rep

REPUTATION_ERROR_FORBIDDEN = "This reputation transaction is not allowed."
REPUTATION_ERROR_GIVER_ID = "A valid giverDiscordId (numeric string) must be provided."
REPUTATION_ERROR_GIVER_TAG = (
    "A valid giverDiscordTag (string with one '#' character) must be provided."
)
REPUTATION_ERROR_RECEIVER_ID = (
    "A valid receiverDiscordId (numeric string) must be provided."
)
REPUTATION_ERROR_RECEIVER_TAG = (
    "A valid receiverDiscordTag (string with one '#' character) must be provided."
)
REPUTATION_ERROR_UNKNOWN = "An unknown error occurred."

logger = logging.getLogger(__name__)


class NewPlusRep(APIView):
    @extend_schema(
        request=PlusRepRequestSerializer,
        responses={
            200: PlusRepResponseSerializer,
            400: PlusRepErrorSerializer,
            403: PlusRepErrorSerializer,
            500: PlusRepErrorSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Creates a PlusRep record and enforces relevant cooldowns.
        """
        giver_discord_id = request.data.get("giverDiscordId")
        if not giver_discord_id or not giver_discord_id.isnumeric():
            serializer = PlusRepErrorSerializer({"error": REPUTATION_ERROR_GIVER_ID})
            return Response(serializer.data, status=400)

        giver_discord_tag = request.data.get("giverDiscordTag")
        if not giver_discord_tag or "#" not in giver_discord_tag:
            serializer = PlusRepErrorSerializer({"error": REPUTATION_ERROR_GIVER_TAG})
            return Response(serializer.data, status=400)

        receiver_discord_id = request.data.get("receiverDiscordId")
        if not receiver_discord_id or not receiver_discord_id.isnumeric():
            serializer = PlusRepErrorSerializer({"error": REPUTATION_ERROR_RECEIVER_ID})
            return Response(serializer.data, status=400)

        receiver_discord_tag = request.data.get("receiverDiscordTag")
        if not receiver_discord_tag or "#" not in receiver_discord_tag:
            serializer = PlusRepErrorSerializer(
                {"error": REPUTATION_ERROR_RECEIVER_TAG}
            )
            return Response(serializer.data, status=400)

        message = request.data.get("message") or ""

        try:
            giver_discord_account = update_or_create_discord_account(
                giver_discord_id, giver_discord_tag, request.user
            )
            receiver_discord_account = update_or_create_discord_account(
                receiver_discord_id, receiver_discord_tag, request.user
            )
            plus_rep = create_new_plus_rep(
                giver_discord_account, receiver_discord_account, message, request.user
            )
            if plus_rep is None:
                serializer = PlusRepErrorSerializer(
                    {"error": REPUTATION_ERROR_FORBIDDEN}
                )
                return Response(serializer.data, status=403)
            serializer = PlusRepResponseSerializer({"success": True})
            return Response(
                data=serializer.data,
                status=200,
            )
        except Exception as ex:
            logger.error(ex)
            serializer = PlusRepErrorSerializer({"error": REPUTATION_ERROR_UNKNOWN})
            return Response(serializer.data, status=500)
