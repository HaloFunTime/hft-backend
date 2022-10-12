import datetime
import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.intern.models import (
    InternChatter,
    InternChatterForbiddenChannel,
    InternChatterPause,
)
from apps.intern.serializers import (
    InternChatterErrorSerializer,
    InternChatterSerializer,
)

logger = logging.getLogger(__name__)

INTERN_CHATTER_DEFAULT_MESSAGE = "Interesting that you'd say that..."
INTERN_CHATTER_ERROR_CHANNEL_FORBIDDEN = (
    "Intern chatter is forbidden in the provided channelId."
)
INTERN_CHATTER_ERROR_INVALID_CHANNEL_ID = (
    "The provided channelId must be a string representing a valid positive integer."
)
INTERN_CHATTER_ERROR_MISSING_CHANNEL_ID = (
    "A channelId must be provided as a query parameter."
)
INTERN_CHATTER_ERROR_PAUSED = "Intern chatter is currently paused."
INTERN_CHATTER_ERROR_UNKNOWN = "An unknown error occurred."


class RandomInternChatter(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="channelId",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            )
        ],
        responses={
            200: InternChatterSerializer,
            400: InternChatterErrorSerializer,
            403: InternChatterErrorSerializer,
            500: InternChatterErrorSerializer,
        },
    )
    def get(self, request, **kwargs):
        """
        Retrieves a random InternChatter if the destination channel isn't forbidden and Intern chatter isn't paused.
        """
        # Validate that there is a passed-in channel ID
        channel_id = request.query_params.get("channelId")
        if channel_id is None:
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_MISSING_CHANNEL_ID}
            )
            return Response(serializer.data, status=400)

        # Validate that the string passed in as a channel ID is numeric
        if not str(channel_id).isnumeric():
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_INVALID_CHANNEL_ID}
            )
            return Response(serializer.data, status=400)

        # If the intended destination channel is forbidden, return an error
        try:
            channels = InternChatterForbiddenChannel.objects.filter(
                discord_channel_id=channel_id
            )
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        if channels.count() > 0:
            logger.debug(f"Chatter is forbidden in channel ${channel_id}")
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_CHANNEL_FORBIDDEN}
            )
            return Response(serializer.data, status=403)

        # If the intern is currently paused, return an error
        try:
            one_hour_ago = datetime.datetime.now() - datetime.timedelta(hours=1)
            pauses = InternChatterPause.objects.filter(created_at__gt=one_hour_ago)
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        if pauses.count() > 0:
            logger.debug("Chatter is currently paused")
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_PAUSED}
            )
            return Response(serializer.data, status=403)

        # Get a random chatter and return it
        random_chatter_message = INTERN_CHATTER_DEFAULT_MESSAGE
        try:
            random_chatters = InternChatter.objects.order_by("?")
            if random_chatters.count() > 0:
                random_chatter_message = random_chatters.first().message_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterErrorSerializer(
                {"error": INTERN_CHATTER_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=404)
        serializer = InternChatterSerializer({"chatter": random_chatter_message})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


# TODO: Accept POSTs that create InternChatterPause records
class PauseInternChatter(APIView):
    pass
