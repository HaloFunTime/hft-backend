import datetime
import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import update_or_create_discord_account
from apps.intern.models import (
    InternChatter,
    InternChatterForbiddenChannel,
    InternChatterPause,
    InternChatterPauseAcceptanceQuip,
    InternChatterPauseDenialQuip,
    InternChatterPauseReverenceQuip,
    InternHelpfulHint,
    InternNewHereWelcomeQuip,
    InternNewHereYeetQuip,
    InternPlusRepQuip,
)
from apps.intern.serializers import (
    InternChatterErrorSerializer,
    InternChatterPauseAcceptanceQuipErrorSerializer,
    InternChatterPauseAcceptanceQuipSerializer,
    InternChatterPauseDenialQuipErrorSerializer,
    InternChatterPauseDenialQuipSerializer,
    InternChatterPauseErrorSerializer,
    InternChatterPauseRequestSerializer,
    InternChatterPauseResponseSerializer,
    InternChatterPauseReverenceQuipErrorSerializer,
    InternChatterPauseReverenceQuipSerializer,
    InternChatterSerializer,
    InternHelpfulHintErrorSerializer,
    InternHelpfulHintSerializer,
    InternNewHereWelcomeQuipErrorSerializer,
    InternNewHereWelcomeQuipSerializer,
    InternNewHereYeetQuipErrorSerializer,
    InternNewHereYeetQuipSerializer,
    InternPlusRepQuipErrorSerializer,
    InternPlusRepQuipSerializer,
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
INTERN_CHATTER_PAUSE_ACCEPTANCE_QUIP_DEFAULT = "Okay."
INTERN_CHATTER_PAUSE_ACCEPTANCE_QUIP_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_CHATTER_PAUSE_DENIAL_QUIP_DEFAULT = "No."
INTERN_CHATTER_PAUSE_DENIAL_QUIP_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_CHATTER_PAUSE_ERROR_MISSING_ID = (
    "A valid discordUserId (numeric string) must be provided."
)
INTERN_CHATTER_PAUSE_ERROR_MISSING_USERNAME = (
    "A valid discordUsername must be provided."
)
INTERN_CHATTER_PAUSE_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_CHATTER_PAUSE_REVERENCE_QUIP_DEFAULT = "Absolutely!"
INTERN_CHATTER_PAUSE_REVERENCE_QUIP_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_HELPFUL_HINT_DEFAULT_MESSAGE = (
    "I do my best to help out by providing helpful hints!"
)
INTERN_HELPFUL_HINT_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_NEW_HERE_WELCOME_QUIP_DEFAULT = "Glad you're here!"
INTERN_NEW_HERE_WELCOME_QUIP_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_NEW_HERE_YEET_QUIP_DEFAULT = "Bye!"
INTERN_NEW_HERE_YEET_QUIP_ERROR_UNKNOWN = "An unknown error occurred."
INTERN_PLUS_REP_QUIP_DEFAULT = "Giving rep is a great way to thank someone."
INTERN_PLUS_REP_QUIP_ERROR_UNKNOWN = "An unknown error occurred."


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
    def get(self, request, *args, **kwargs):
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


class RandomInternChatterPauseAcceptanceQuip(APIView):
    @extend_schema(
        responses={
            200: InternChatterPauseAcceptanceQuipSerializer,
            500: InternChatterPauseAcceptanceQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternChatterPauseAcceptanceQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_CHATTER_PAUSE_ACCEPTANCE_QUIP_DEFAULT
        try:
            random_quips = InternChatterPauseAcceptanceQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterPauseAcceptanceQuipErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_ACCEPTANCE_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternChatterPauseAcceptanceQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class RandomInternChatterPauseDenialQuip(APIView):
    @extend_schema(
        responses={
            200: InternChatterPauseDenialQuipSerializer,
            500: InternChatterPauseDenialQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternChatterPauseDenialQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_CHATTER_PAUSE_DENIAL_QUIP_DEFAULT
        try:
            random_quips = InternChatterPauseDenialQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterPauseDenialQuipErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_DENIAL_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternChatterPauseDenialQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class RandomInternChatterPauseReverenceQuip(APIView):
    @extend_schema(
        responses={
            200: InternChatterPauseReverenceQuipSerializer,
            500: InternChatterPauseReverenceQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternChatterPauseReverenceQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_CHATTER_PAUSE_REVERENCE_QUIP_DEFAULT
        try:
            random_quips = InternChatterPauseReverenceQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterPauseReverenceQuipErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_REVERENCE_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternChatterPauseReverenceQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class RandomInternNewHereWelcomeQuip(APIView):
    @extend_schema(
        responses={
            200: InternNewHereWelcomeQuipSerializer,
            500: InternNewHereWelcomeQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternNewHereWelcomeQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_NEW_HERE_WELCOME_QUIP_DEFAULT
        try:
            random_quips = InternNewHereWelcomeQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternNewHereWelcomeQuipErrorSerializer(
                {"error": INTERN_NEW_HERE_WELCOME_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternNewHereWelcomeQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class RandomInternNewHereYeetQuip(APIView):
    @extend_schema(
        responses={
            200: InternNewHereYeetQuipSerializer,
            500: InternNewHereYeetQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternNewHereYeetQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_NEW_HERE_YEET_QUIP_DEFAULT
        try:
            random_quips = InternNewHereYeetQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternNewHereYeetQuipErrorSerializer(
                {"error": INTERN_NEW_HERE_YEET_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternNewHereYeetQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class RandomInternPlusRepQuip(APIView):
    @extend_schema(
        responses={
            200: InternPlusRepQuipSerializer,
            500: InternPlusRepQuipErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternPlusRepQuip.
        """
        # Get a random quip and return it
        random_quip = INTERN_PLUS_REP_QUIP_DEFAULT
        try:
            random_quips = InternPlusRepQuip.objects.order_by("?")
            if random_quips.count() > 0:
                random_quip = random_quips.first().quip_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternPlusRepQuipErrorSerializer(
                {"error": INTERN_PLUS_REP_QUIP_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)
        serializer = InternPlusRepQuipSerializer({"quip": random_quip})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


class PauseInternChatter(APIView):
    @extend_schema(
        request=InternChatterPauseRequestSerializer,
        responses={
            200: InternChatterPauseResponseSerializer,
            400: InternChatterPauseErrorSerializer,
            500: InternChatterPauseErrorSerializer,
        },
    )
    def post(self, request, *args, **kwargs):
        """
        Creates an InternChatterPause record.
        """
        discord_user_id = request.data.get("discordUserId")
        if not discord_user_id or not discord_user_id.isnumeric():
            serializer = InternChatterPauseErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_ID}
            )
            return Response(serializer.data, status=400)
        discord_username = request.data.get("discordUsername")
        if (
            not discord_username
            or len(discord_username) < 2
            or len(discord_username) > 32
        ):
            serializer = InternChatterPauseErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_ERROR_MISSING_USERNAME}
            )
            return Response(serializer.data, status=400)
        try:
            pauser = update_or_create_discord_account(
                discord_user_id, discord_username, request.user
            )
            InternChatterPause.objects.create(
                creator=request.user,
                pauser=pauser,
            )
            serializer = InternChatterPauseResponseSerializer({"success": True})
            return Response(
                data=serializer.data,
                status=200,
            )
        except Exception as ex:
            logger.error(ex)
            serializer = InternChatterPauseErrorSerializer(
                {"error": INTERN_CHATTER_PAUSE_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=500)


class RandomInternHelpfulHint(APIView):
    @extend_schema(
        responses={
            200: InternHelpfulHintSerializer,
            400: InternHelpfulHintErrorSerializer,
            403: InternHelpfulHintErrorSerializer,
            500: InternHelpfulHintErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves a random InternHelpfulHint.
        """
        # Get a random helpful hint and return it
        random_helpful_hint = INTERN_HELPFUL_HINT_DEFAULT_MESSAGE
        try:
            random_hints = InternHelpfulHint.objects.order_by("?")
            if random_hints.count() > 0:
                random_helpful_hint = random_hints.first().message_text
        except Exception as ex:
            logger.error(ex)
            serializer = InternHelpfulHintErrorSerializer(
                {"error": INTERN_HELPFUL_HINT_ERROR_UNKNOWN}
            )
            return Response(serializer.data, status=404)
        serializer = InternHelpfulHintSerializer({"hint": random_helpful_hint})
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )
