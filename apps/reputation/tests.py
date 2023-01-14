import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.discord.utils import update_or_create_discord_account
from apps.reputation.models import PlusRep
from apps.reputation.utils import (
    can_giver_send_rep,
    can_giver_send_rep_to_receiver,
    check_past_year_rep,
    count_plus_rep_given_in_current_week,
    get_current_week_start_time,
    get_time_until_reset,
    get_week_start_time,
)
from apps.reputation.views import (
    REPUTATION_ERROR_FORBIDDEN,
    REPUTATION_ERROR_GIVER_ID,
    REPUTATION_ERROR_GIVER_TAG,
    REPUTATION_ERROR_INVALID_DISCORD_ID,
    REPUTATION_ERROR_MISSING_DISCORD_ID,
    REPUTATION_ERROR_RECEIVER_ID,
    REPUTATION_ERROR_RECEIVER_TAG,
)


def plus_rep_factory(
    creator: User, giver: DiscordAccount, receiver: DiscordAccount, message: str = ""
):
    return PlusRep.objects.create(
        creator=creator, giver=giver, receiver=receiver, message=message
    )


class CheckRepTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.reputation.views.get_time_until_reset")
    @patch("apps.reputation.views.count_plus_rep_given_in_current_week")
    @patch("apps.reputation.views.check_past_year_rep")
    def test_check_rep(
        self,
        mock_check_past_year_rep,
        mock_count_plus_rep_given_in_current_week,
        mock_get_time_until_reset,
    ):
        # Missing 'discordId' throws error
        response = self.client.get("/reputation/check-rep")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_MISSING_DISCORD_ID})

        # Non-numeric 'discordId' throws error
        response = self.client.get("/reputation/check-rep?discordId=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_INVALID_DISCORD_ID})

        account = update_or_create_discord_account("1234", "Foo#1234", self.user)

        # Happy path - all plurals
        mock_check_past_year_rep.return_value = (12, 3)
        mock_count_plus_rep_given_in_current_week.return_value = 2
        mock_get_time_until_reset.return_value = datetime.timedelta(
            days=2, hours=3, minutes=4, seconds=5
        )
        response = self.client.get(
            f"/reputation/check-rep?discordId={account.discord_id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pastYearTotalRep"), 12)
        self.assertEqual(response.data.get("pastYearUniqueRep"), 3)
        self.assertEqual(response.data.get("thisWeekRepGiven"), 2)
        self.assertEqual(
            response.data.get("thisWeekRepReset"),
            "2 days, 3 hours, 4 minutes, 5 seconds",
        )

        # Happy path - all singular
        mock_check_past_year_rep.return_value = (12, 3)
        mock_count_plus_rep_given_in_current_week.return_value = 2
        mock_get_time_until_reset.return_value = datetime.timedelta(
            days=1, hours=1, minutes=1, seconds=1
        )
        response = self.client.get(
            f"/reputation/check-rep?discordId={account.discord_id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pastYearTotalRep"), 12)
        self.assertEqual(response.data.get("pastYearUniqueRep"), 3)
        self.assertEqual(response.data.get("thisWeekRepGiven"), 2)
        self.assertEqual(
            response.data.get("thisWeekRepReset"),
            "1 day, 1 hour, 1 minute, 1 second",
        )

        # Happy path - string fully omitted
        mock_check_past_year_rep.return_value = (12, 3)
        mock_count_plus_rep_given_in_current_week.return_value = 2
        mock_get_time_until_reset.return_value = datetime.timedelta(
            days=0, hours=0, minutes=0, seconds=0
        )
        response = self.client.get(
            f"/reputation/check-rep?discordId={account.discord_id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("pastYearTotalRep"), 12)
        self.assertEqual(response.data.get("pastYearUniqueRep"), 3)
        self.assertEqual(response.data.get("thisWeekRepGiven"), 2)
        self.assertEqual(
            response.data.get("thisWeekRepReset"),
            "",
        )


class PlusRepTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.reputation.utils.can_giver_send_rep_to_receiver")
    @patch("apps.reputation.utils.can_giver_send_rep")
    def test_plus_rep(
        self, mock_can_giver_send_rep, mock_can_giver_send_rep_to_receiver
    ):
        mock_can_giver_send_rep.return_value = True
        mock_can_giver_send_rep_to_receiver.return_value = True

        # Missing 'giverDiscordId' throws error
        response = self.client.post("/reputation/plus-rep", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_GIVER_ID})

        # Non-numeric 'giverDiscordId' throws error
        response = self.client.post(
            "/reputation/plus-rep", {"giverDiscordId": "abc"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_GIVER_ID})

        # Missing 'giverDiscordTag' throws error
        response = self.client.post(
            "/reputation/plus-rep", {"giverDiscordId": "1234"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_GIVER_TAG})

        # Invalid 'giverDiscordTag' throws error
        response = self.client.post(
            "/reputation/plus-rep",
            {"giverDiscordId": "1234", "giverDiscordTag": "foo"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_GIVER_TAG})

        # Missing 'receiverDiscordId' throws error
        response = self.client.post(
            "/reputation/plus-rep",
            {"giverDiscordId": "1234", "giverDiscordTag": "HFTIntern#1234"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_RECEIVER_ID})

        # Non-numeric 'receiverDiscordId' throws error
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_RECEIVER_ID})

        # Missing 'receiverDiscordTag' throws error
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "1234",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_RECEIVER_TAG})

        # Invalid 'receiverDiscordTag' throws error
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "1234",
                "receiverDiscordTag": "foo",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_RECEIVER_TAG})

        # 1: Valid data (excluding 'message') succeeds
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "5678",
                "receiverDiscordTag": "HFTIntern#5678",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertEqual(PlusRep.objects.count(), 1)
        plus_rep_1 = PlusRep.objects.order_by("-created_at").first()
        self.assertEqual(plus_rep_1.giver.discord_id, "1234")
        self.assertEqual(plus_rep_1.giver.discord_tag, "HFTIntern#1234")
        self.assertEqual(plus_rep_1.receiver.discord_id, "5678")
        self.assertEqual(plus_rep_1.receiver.discord_tag, "HFTIntern#5678")
        self.assertEqual(plus_rep_1.message, "")

        # 2: Valid data succeeds
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "6789",
                "receiverDiscordTag": "HFTIntern#6789",
                "message": "I think Halo is a pretty cool guy. Eh kills aleins and doesnt afraid of anything.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertEqual(PlusRep.objects.count(), 2)
        plus_rep_2 = PlusRep.objects.order_by("-created_at").first()
        self.assertEqual(plus_rep_2.giver.discord_id, "1234")
        self.assertEqual(plus_rep_2.giver.discord_tag, "HFTIntern#1234")
        self.assertEqual(plus_rep_2.receiver.discord_id, "6789")
        self.assertEqual(plus_rep_2.receiver.discord_tag, "HFTIntern#6789")
        self.assertEqual(
            plus_rep_2.message,
            "I think Halo is a pretty cool guy. Eh kills aleins and doesnt afraid of anything.",
        )

        # 3: Valid data (with null 'message') succeeds
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "7890",
                "receiverDiscordTag": "HFTIntern#7890",
                "message": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"success": True})
        self.assertEqual(PlusRep.objects.count(), 3)
        plus_rep_3 = PlusRep.objects.order_by("-created_at").first()
        self.assertEqual(plus_rep_3.giver.discord_id, "1234")
        self.assertEqual(plus_rep_3.giver.discord_tag, "HFTIntern#1234")
        self.assertEqual(plus_rep_3.receiver.discord_id, "7890")
        self.assertEqual(plus_rep_3.receiver.discord_tag, "HFTIntern#7890")
        self.assertEqual(plus_rep_3.message, "")

        # 4: 403 if giver cannot send rep - no record created
        mock_can_giver_send_rep.return_value = False
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "7890",
                "receiverDiscordTag": "HFTIntern#7890",
                "message": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_FORBIDDEN})
        self.assertEqual(PlusRep.objects.count(), 3)

        # 5: 403 if giver cannot send rep to receiver - no record created
        mock_can_giver_send_rep.return_value = True
        mock_can_giver_send_rep_to_receiver.return_value = False
        response = self.client.post(
            "/reputation/plus-rep",
            {
                "giverDiscordId": "1234",
                "giverDiscordTag": "HFTIntern#1234",
                "receiverDiscordId": "7890",
                "receiverDiscordTag": "HFTIntern#7890",
                "message": None,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, {"error": REPUTATION_ERROR_FORBIDDEN})
        self.assertEqual(PlusRep.objects.count(), 3)


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.reputation.utils.count_plus_rep_given_in_current_week")
    def test_can_giver_send_rep(self, mock_count_plus_rep_given_in_current_week):
        giver = update_or_create_discord_account("1234", "ABCD#1234", self.user)
        # Rep can be sent if a Discord Account has not yet sent any in the current week
        mock_count_plus_rep_given_in_current_week.return_value = 0
        self.assertTrue(can_giver_send_rep(giver))

        # Rep can be sent if a Discord Account has sent one rep so far in the current week
        mock_count_plus_rep_given_in_current_week.return_value = 1
        self.assertTrue(can_giver_send_rep(giver))

        # Rep can be sent if a Discord Account has sent two reps so far in the current week
        mock_count_plus_rep_given_in_current_week.return_value = 2
        self.assertTrue(can_giver_send_rep(giver))

        # Rep cannot be sent if a Discord Account has sent three reps so far in the current week
        mock_count_plus_rep_given_in_current_week.return_value = 3
        self.assertFalse(can_giver_send_rep(giver))

    @patch("apps.reputation.utils.get_current_week_start_time")
    def test_can_giver_send_rep_to_receiver(self, mock_get_current_week_start_time):
        giver = update_or_create_discord_account("1234", "ABCD#1234", self.user)
        receiver = update_or_create_discord_account("5678", "EFGH#5678", self.user)
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        # Rep cannot be sent from a Discord Account to itself
        self.assertFalse(can_giver_send_rep_to_receiver(giver, giver))
        self.assertFalse(can_giver_send_rep_to_receiver(receiver, receiver))

        # Rep can be sent if a Discord Account has not yet sent any to the receiver
        self.assertTrue(can_giver_send_rep_to_receiver(giver, receiver))

        # Rep can be sent if a Discord Account has sent one rep so far to the receiver, but in a previous week
        plus_rep_old = plus_rep_factory(self.user, giver, receiver)
        plus_rep_old.created_at = datetime.datetime.fromisoformat(
            "2023-12-27T11:00:00-07:00"
        )
        plus_rep_old.save()
        self.assertTrue(can_giver_send_rep_to_receiver(giver, receiver))

        # Rep cannot be sent if a Discord Account has sent one rep so far to the receiver in the current week
        plus_rep_1 = plus_rep_factory(self.user, giver, receiver)
        plus_rep_1.created_at = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        plus_rep_1.save()
        self.assertFalse(can_giver_send_rep_to_receiver(giver, receiver))

        # Rep can be sent the following week (when no rep has been sent yet)
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-10T11:00:00-07:00"
        )
        self.assertTrue(can_giver_send_rep_to_receiver(giver, receiver))

    @patch("apps.reputation.utils.get_current_time")
    def test_check_past_year_rep(self, mock_get_current_time):
        # Rep given on the first of every month in 2022, evaluated from Jan 3 2023, unique givers
        mock_get_current_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        receiver = update_or_create_discord_account("1234", "ABCD#1234", self.user)
        for i in range(1, 13):
            giver = update_or_create_discord_account(str(i), "Test#1234", self.user)
            plus_rep = plus_rep_factory(self.user, giver, receiver)
            plus_rep.created_at = datetime.datetime.fromisoformat(
                f"2022-{str(i).rjust(2, '0')}-01T00:00:00-07:00"
            )
            plus_rep.save()
        result = check_past_year_rep(receiver)
        self.assertEqual(result[0], 11)
        self.assertEqual(result[1], 11)

        # Rep given on the first of every month in 2022, evaluated from Jan 3 2023, nonunique givers
        mock_get_current_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        receiver = update_or_create_discord_account("2345", "ABCD#1234", self.user)
        giver = update_or_create_discord_account("0123", "Test#1234", self.user)
        for i in range(1, 13):
            plus_rep = plus_rep_factory(self.user, giver, receiver)
            plus_rep.created_at = datetime.datetime.fromisoformat(
                f"2022-{str(i).rjust(2, '0')}-01T00:00:00-07:00"
            )
            plus_rep.save()
        result = check_past_year_rep(receiver)
        self.assertEqual(result[0], 11)
        self.assertEqual(result[1], 1)

    @patch("apps.reputation.utils.get_current_week_start_time")
    def test_count_plus_rep_given_in_current_week(
        self, mock_get_current_week_start_time
    ):
        giver = update_or_create_discord_account("1234", "ABCD#1234", self.user)
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        # Rep given in current week should start at zero
        self.assertEqual(count_plus_rep_given_in_current_week(giver), 0)

        # One record saved during the week should result in the method returning 1
        plus_rep_1 = plus_rep_factory(self.user, giver, giver)
        plus_rep_1.created_at = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        plus_rep_1.save()
        self.assertEqual(count_plus_rep_given_in_current_week(giver), 1)

        # Two records saved during the week should result in the method returning 2
        plus_rep_2 = plus_rep_factory(self.user, giver, giver)
        plus_rep_2.created_at = datetime.datetime.fromisoformat(
            "2023-01-05T18:30:54-07:00"
        )
        plus_rep_2.save()
        self.assertEqual(count_plus_rep_given_in_current_week(giver), 2)

        # Three records saved during the week should result in the method returning 3
        plus_rep_3 = plus_rep_factory(self.user, giver, giver)
        plus_rep_3.created_at = datetime.datetime.fromisoformat(
            "2023-01-07T22:46:04-07:00"
        )
        plus_rep_3.save()
        self.assertEqual(count_plus_rep_given_in_current_week(giver), 3)

        # Checking a future week with no saved rep should result in the method returning zero
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-10T11:00:00-07:00"
        )
        self.assertEqual(count_plus_rep_given_in_current_week(giver), 0)

    @patch("apps.reputation.utils.get_current_time")
    def test_get_current_week_start_time(self, mock_get_current_time):
        expected_tuples = [
            # Basic example
            ("2023-01-04T10:34:27-07:00", "2023-01-03T11:00:00-07:00"),
            # Week starts in previous month
            ("2023-02-02T02:34:27-07:00", "2023-01-31T11:00:00-07:00"),
            # Week starts in previous year
            ("2023-01-01T10:00:00-07:00", "2022-12-27T11:00:00-07:00"),
            # Week starts this instant
            ("2023-01-03T11:00:00-07:00", "2023-01-03T11:00:00-07:00"),
            # Week starts one microsecond ago
            ("2023-01-03T11:00:00.000001-07:00", "2023-01-03T11:00:00-07:00"),
            # Last microsecond of week
            ("2023-01-03T10:59:59.999999-07:00", "2022-12-27T11:00:00-07:00"),
        ]
        for expected_tuple in expected_tuples:
            mock_get_current_time.return_value = datetime.datetime.fromisoformat(
                expected_tuple[0]
            )
            self.assertEqual(
                get_current_week_start_time(),
                datetime.datetime.fromisoformat(expected_tuple[1]),
            )

    @patch("apps.reputation.utils.get_current_time")
    def test_get_time_until_reset(self, mock_get_current_time):
        expected_tuples = [
            # Basic example
            (
                "2023-01-04T10:34:27-07:00",
                datetime.timedelta(days=6, seconds=1533, microseconds=0),
            ),
            # Reset in next month
            (
                "2023-03-29T02:34:27-07:00",
                datetime.timedelta(days=6, seconds=30333, microseconds=0),
            ),
            # Reset in next year
            (
                "2022-12-28T10:00:00-07:00",
                datetime.timedelta(days=6, seconds=3600, microseconds=0),
            ),
            # Reset just refreshed
            (
                "2023-01-03T11:00:00-07:00",
                datetime.timedelta(days=7, seconds=0, microseconds=0),
            ),
            # Reset just refreshed and one microsecond passed
            (
                "2023-01-03T11:00:00.000001-07:00",
                datetime.timedelta(days=6, seconds=86399, microseconds=999999),
            ),
            # Reset one microsecond from refreshing
            (
                "2023-01-03T10:59:59.999999-07:00",
                datetime.timedelta(days=0, seconds=0, microseconds=1),
            ),
        ]
        for expected_tuple in expected_tuples:
            mock_get_current_time.return_value = datetime.datetime.fromisoformat(
                expected_tuple[0]
            )
            self.assertEqual(get_time_until_reset(), expected_tuple[1])

    def test_get_week_start_time(self):
        expected_tuples = [
            # Basic example
            ("2023-01-04T10:34:27-07:00", "2023-01-03T11:00:00-07:00"),
            # Week starts in previous month
            ("2023-02-02T02:34:27-07:00", "2023-01-31T11:00:00-07:00"),
            # Week starts in previous year
            ("2023-01-01T10:00:00-07:00", "2022-12-27T11:00:00-07:00"),
            # Week starts this instant
            ("2023-01-03T11:00:00-07:00", "2023-01-03T11:00:00-07:00"),
            # Week starts one microsecond ago
            ("2023-01-03T11:00:00.000001-07:00", "2023-01-03T11:00:00-07:00"),
            # Last microsecond of week
            ("2023-01-03T10:59:59.999999-07:00", "2022-12-27T11:00:00-07:00"),
        ]
        for expected_tuple in expected_tuples:
            self.assertEqual(
                get_week_start_time(datetime.datetime.fromisoformat(expected_tuple[0])),
                datetime.datetime.fromisoformat(expected_tuple[1]),
            )
