import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.discord.utils import update_or_create_discord_account
from apps.reputation.models import PlusRep
from apps.reputation.utils import (
    can_giver_send_rep,
    can_giver_send_rep_to_receiver,
    get_current_week_start_time,
)
from apps.reputation.views import (
    REPUTATION_ERROR_FORBIDDEN,
    REPUTATION_ERROR_GIVER_ID,
    REPUTATION_ERROR_GIVER_TAG,
    REPUTATION_ERROR_RECEIVER_ID,
    REPUTATION_ERROR_RECEIVER_TAG,
)


def plus_rep_factory(
    creator: User, giver: DiscordAccount, receiver: DiscordAccount, message: str = ""
):
    return PlusRep.objects.create(
        creator=creator, giver=giver, receiver=receiver, message=message
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

    @patch("apps.reputation.utils.get_current_week_start_time")
    def test_can_giver_send_rep(self, mock_get_current_week_start_time):
        giver = update_or_create_discord_account("1234", "ABCD#1234", self.user)
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        # Rep can be sent if a Discord Account has not yet sent any in the current week
        self.assertTrue(can_giver_send_rep(giver))

        # Rep can be sent if a Discord Account has sent one rep so far in the current week
        plus_rep_1 = plus_rep_factory(self.user, giver, giver)
        plus_rep_1.created_at = datetime.datetime.fromisoformat(
            "2023-01-03T11:00:00-07:00"
        )
        plus_rep_1.save()
        self.assertTrue(can_giver_send_rep(giver))

        # Rep can be sent if a Discord Account has sent two reps so far in the current week
        plus_rep_2 = plus_rep_factory(self.user, giver, giver)
        plus_rep_2.created_at = datetime.datetime.fromisoformat(
            "2023-01-05T18:30:54-07:00"
        )
        plus_rep_2.save()
        self.assertTrue(can_giver_send_rep(giver))

        # Rep cannot be sent if a Discord Account has sent three reps so far in the current week
        plus_rep_3 = plus_rep_factory(self.user, giver, giver)
        plus_rep_3.created_at = datetime.datetime.fromisoformat(
            "2023-01-07T22:46:04-07:00"
        )
        plus_rep_3.save()
        self.assertFalse(can_giver_send_rep(giver))

        # Rep can be sent the following week (when no rep has been sent yet)
        mock_get_current_week_start_time.return_value = datetime.datetime.fromisoformat(
            "2023-01-10T11:00:00-07:00"
        )
        self.assertTrue(can_giver_send_rep(giver))

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
