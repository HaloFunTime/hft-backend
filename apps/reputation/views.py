import logging

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.discord.utils import (
    get_or_create_discord_account,
    update_or_create_discord_account,
)
from apps.reputation.serializers import (
    CheckRepErrorSerializer,
    CheckRepResponseSerializer,
    PlusRepErrorSerializer,
    PlusRepRequestSerializer,
    PlusRepResponseSerializer,
    TopRepErrorSerializer,
    TopRepResponseSerializer,
    TopRepSerializer,
)
from apps.reputation.utils import (
    check_past_year_rep,
    count_plus_rep_given_in_current_week,
    create_new_plus_rep,
    get_time_until_reset,
    get_top_rep_past_year,
)

REPUTATION_ERROR_FORBIDDEN = "This reputation transaction is not allowed."
REPUTATION_ERROR_GIVER_ID = "A valid giverDiscordId (numeric string) must be provided."
REPUTATION_ERROR_GIVER_USERNAME = "A valid giverDiscordUsername must be provided."
REPUTATION_ERROR_INVALID_COUNT = (
    "The provided count must be a valid non-negative integer."
)
REPUTATION_ERROR_INVALID_DISCORD_ID = (
    "The provided discordId must be a string representing a valid positive integer."
)
REPUTATION_ERROR_MISSING_DISCORD_ID = (
    "A discordId must be provided as a query parameter."
)
REPUTATION_ERROR_RECEIVER_ID = (
    "A valid receiverDiscordId (numeric string) must be provided."
)
REPUTATION_ERROR_RECEIVER_USERNAME = "A valid receiverDiscordUsername must be provided."
REPUTATION_ERROR_UNKNOWN = "An unknown error occurred."

logger = logging.getLogger(__name__)


class CheckRep(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="discordId",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                required=True,
                style="form",
                explode=False,
            )
        ],
        responses={
            200: CheckRepResponseSerializer,
            400: CheckRepErrorSerializer,
            404: CheckRepErrorSerializer,
            500: CheckRepErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves rep data for a given Discord Account.
        """
        # Validate that there is a passed-in Discord Account ID
        discord_account_id = request.query_params.get("discordId")
        if discord_account_id is None:
            serializer = CheckRepErrorSerializer(
                {"error": REPUTATION_ERROR_MISSING_DISCORD_ID}
            )
            return Response(serializer.data, status=400)

        # Validate that the string passed in as a channel ID is numeric
        if not str(discord_account_id).isnumeric():
            serializer = CheckRepErrorSerializer(
                {"error": REPUTATION_ERROR_INVALID_DISCORD_ID}
            )
            return Response(serializer.data, status=400)

        # Get the Discord Account
        discord_account = get_or_create_discord_account(
            discord_account_id, request.user
        )

        # Get relevant rep amounts
        yearly_rep = check_past_year_rep(discord_account)
        this_week_rep_given = count_plus_rep_given_in_current_week(discord_account)

        # Build the reset string
        next_reset = get_time_until_reset()
        total_seconds = next_reset.seconds
        hours = 0
        while total_seconds >= 3600:
            total_seconds -= 3600
            hours += 1
        minutes = 0
        while total_seconds >= 60:
            total_seconds -= 60
            minutes += 1
        reset_data = []
        if next_reset.days > 1:
            reset_data.append(f"{next_reset.days} days")
        elif next_reset.days == 1:
            reset_data.append(f"{next_reset.days} day")
        if hours > 1:
            reset_data.append(f"{hours} hours")
        elif hours == 1:
            reset_data.append(f"{hours} hour")
        if minutes > 1:
            reset_data.append(f"{minutes} minutes")
        elif minutes == 1:
            reset_data.append(f"{minutes} minute")
        if total_seconds > 1:
            reset_data.append(f"{total_seconds} seconds")
        elif total_seconds == 1:
            reset_data.append(f"{total_seconds} second")

        # Return the relevant rep data
        serializer = CheckRepResponseSerializer(
            {
                "pastYearTotalRep": yearly_rep[0],
                "pastYearUniqueRep": yearly_rep[1],
                "thisWeekRepGiven": this_week_rep_given,
                "thisWeekRepReset": ", ".join(reset_data),
            }
        )
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )


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

        giver_discord_username = request.data.get("giverDiscordUsername")
        if (
            not giver_discord_username
            or len(giver_discord_username) < 2
            or len(giver_discord_username) > 32
        ):
            serializer = PlusRepErrorSerializer(
                {"error": REPUTATION_ERROR_GIVER_USERNAME}
            )
            return Response(serializer.data, status=400)

        receiver_discord_id = request.data.get("receiverDiscordId")
        if not receiver_discord_id or not receiver_discord_id.isnumeric():
            serializer = PlusRepErrorSerializer({"error": REPUTATION_ERROR_RECEIVER_ID})
            return Response(serializer.data, status=400)

        receiver_discord_username = request.data.get("receiverDiscordUsername")
        if (
            not receiver_discord_username
            or len(receiver_discord_username) < 2
            or len(receiver_discord_username) > 32
        ):
            serializer = PlusRepErrorSerializer(
                {"error": REPUTATION_ERROR_RECEIVER_USERNAME}
            )
            return Response(serializer.data, status=400)

        message = request.data.get("message") or ""

        try:
            giver_discord_account = update_or_create_discord_account(
                giver_discord_id, giver_discord_username, request.user
            )
            receiver_discord_account = update_or_create_discord_account(
                receiver_discord_id, receiver_discord_username, request.user
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


class TopRep(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="count",
                type={"type": "integer"},
                location=OpenApiParameter.QUERY,
                required=False,
                style="form",
                explode=False,
            ),
            OpenApiParameter(
                name="excludeIds",
                type={"type": "string"},
                location=OpenApiParameter.QUERY,
                required=False,
                style="form",
                explode=False,
            ),
        ],
        responses={
            200: TopRepResponseSerializer,
            400: TopRepErrorSerializer,
            404: TopRepErrorSerializer,
            500: TopRepErrorSerializer,
        },
    )
    def get(self, request, *args, **kwargs):
        """
        Retrieves the top `count` DiscordAccounts, ordered by PlusRep received in the past year.
        """
        # Check whether count was specified
        count = request.query_params.get("count")
        if count is None:
            count = 10  # Default to returning 10

        # Validate that count is numeric and non-negative
        invalid_count = False
        try:
            count = int(count)
            if count < 0:
                invalid_count = True
        except ValueError:
            invalid_count = True
        if invalid_count:
            serializer = TopRepErrorSerializer(
                {"error": REPUTATION_ERROR_INVALID_COUNT}
            )
            return Response(serializer.data, status=400)

        # Check whether excludeIds was specified
        excludeIds = request.query_params.get("excludeIds")
        if excludeIds is None:
            excludeIds = []  # Default to empty list
        elif excludeIds == "":
            excludeIds = []  # Default to empty list
        else:
            excludeIds = excludeIds.split(",")

        # Retrieve the top `count` DiscordAccounts, ordered by total_rep and excluding `excludeIds`
        top_accounts = get_top_rep_past_year(count, excludeIds)

        # Build the serialized result
        top_reps = []
        for account in top_accounts:
            top_reps.append(
                TopRepSerializer(
                    {
                        "rank": account.rank,
                        "discordId": account.discord_id,
                        "pastYearTotalRep": account.total_rep,
                        "pastYearUniqueRep": account.unique_rep,
                    }
                )
            )
        serializer = TopRepResponseSerializer(
            {"topRepReceivers": [top_rep.data for top_rep in top_reps]}
        )
        return Response(
            serializer.data, status=200, headers={"Cache-Control": "no-cache"}
        )
