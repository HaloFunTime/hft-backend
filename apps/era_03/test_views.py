import datetime

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.era_03.models import BoatCaptain, BoatDeckhand, BoatRank


class Era03TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)
        self.first_rank = BoatRank.objects.create(
            creator=self.user,
            rank="Junior Deckhand",
            tier=1,
            track="N/A",
            description="The lowest rank in the crew. Responsible for sweeping the poop deck.",
        )

    def test_board_boat_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/board-boat", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-03/board-boat",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # New deckhand
        response = self.client.post(
            "/era-03/board-boat",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), True)
        self.assertEqual(response.data.get("rank"), "Junior Deckhand")
        self.assertEqual(BoatDeckhand.objects.all().count(), 1)
        deckhand_record = BoatDeckhand.objects.first()
        self.assertEqual(deckhand_record.deckhand_id, "123")
        self.assertEqual(deckhand_record.rank, self.first_rank)

        # Existing deckhand
        response = self.client.post(
            "/era-03/board-boat",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), False)
        self.assertEqual(response.data.get("rank"), "Junior Deckhand")
        self.assertEqual(BoatDeckhand.objects.all().count(), 1)
        deckhand_record = BoatDeckhand.objects.first()
        self.assertEqual(deckhand_record.deckhand_id, "123")
        self.assertEqual(deckhand_record.rank, self.first_rank)

    def test_save_captain_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/save-boat-captain", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("rankTier", details)
        self.assertEqual(
            details.get("rankTier"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "rankTier": "not_an_int",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("rankTier", details)
        self.assertEqual(
            details.get("rankTier")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New captain
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "rankTier": 3,
            },
            format="json",
        )
        self.assertEqual(BoatCaptain.objects.all().count(), 1)
        captain_record = BoatCaptain.objects.first()
        self.assertEqual(captain_record.earner_id, "123")
        self.assertGreaterEqual(captain_record.earned_at, now_before_post)
        self.assertEqual(captain_record.rank_tier, 3)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBoatCaptain"), True)
        initial_earned_at = captain_record.earned_at

        # Existing captain, rank tier update
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "rankTier": 4,
            },
            format="json",
        )
        self.assertEqual(BoatCaptain.objects.all().count(), 1)
        captain_record = BoatCaptain.objects.first()
        self.assertEqual(captain_record.earner_id, "123")
        self.assertGreaterEqual(captain_record.earned_at, initial_earned_at)
        self.assertEqual(captain_record.rank_tier, 4)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBoatCaptain"), False)

    def test_check_deckhand_games_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/check-deckhand-games", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-03/check-deckhand-games",
            {
                "discordUserIds": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds")[0],
            ErrorDetail(
                string='Expected a list of items but got type "str".', code="not_a_list"
            ),
        )
