import datetime

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.season_06.models import BingoBuff, BingoChallengeParticipant


class Season06TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_join_challenge_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-06/join-challenge", {}, format="json")
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
            "/season-06/join-challenge",
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

        # New participant
        response = self.client.post(
            "/season-06/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), True)
        self.assertIsNotNone(response.data.get("boardOrder"))
        self.assertEqual(BingoChallengeParticipant.objects.all().count(), 1)
        participant_record = BingoChallengeParticipant.objects.first()
        self.assertEqual(participant_record.participant_id, "123")
        self.assertIsNotNone(participant_record.board_order)
        initial_board_order = participant_record.board_order

        # Existing participant
        response = self.client.post(
            "/season-06/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), False)
        self.assertIsNotNone(response.data.get("boardOrder"))
        self.assertEqual(BingoChallengeParticipant.objects.all().count(), 1)
        participant_record = BingoChallengeParticipant.objects.first()
        self.assertEqual(participant_record.participant_id, "123")
        self.assertIsNotNone(participant_record.board_order)
        self.assertEqual(initial_board_order, participant_record.board_order)

    def test_save_buff_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-06/save-buff", {}, format="json")
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
        self.assertIn("bingoCount", details)
        self.assertEqual(
            details.get("bingoCount"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("challengeCount", details)
        self.assertEqual(
            details.get("challengeCount"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-06/save-buff",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "bingoCount": "not_an_int",
                "challengeCount": "not_an_int",
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
        self.assertIn("bingoCount", details)
        self.assertEqual(
            details.get("bingoCount")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )
        self.assertIn("challengeCount", details)
        self.assertEqual(
            details.get("challengeCount")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New buff
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/season-06/save-buff",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "bingoCount": 3,
                "challengeCount": 12,
            },
            format="json",
        )
        self.assertEqual(BingoBuff.objects.all().count(), 1)
        buff_record = BingoBuff.objects.first()
        self.assertEqual(buff_record.earner_id, "123")
        self.assertGreaterEqual(buff_record.earned_at, now_before_post)
        self.assertEqual(buff_record.bingo_count, 3)
        self.assertEqual(buff_record.challenge_count, 12)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBuff"), True)
        self.assertEqual(response.data.get("blackout"), False)
        initial_earned_at = buff_record.earned_at

        # Existing buff, bingo/challenge count update
        response = self.client.post(
            "/season-06/save-buff",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "bingoCount": 4,
                "challengeCount": 18,
            },
            format="json",
        )
        self.assertEqual(BingoBuff.objects.all().count(), 1)
        buff_record = BingoBuff.objects.first()
        self.assertEqual(buff_record.earner_id, "123")
        self.assertGreaterEqual(buff_record.earned_at, initial_earned_at)
        self.assertEqual(buff_record.bingo_count, 4)
        self.assertEqual(buff_record.challenge_count, 18)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBuff"), False)
        self.assertEqual(response.data.get("blackout"), False)

        # Existing buff, blackout
        response = self.client.post(
            "/season-06/save-buff",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "bingoCount": 12,
                "challengeCount": 25,
            },
            format="json",
        )
        self.assertEqual(BingoBuff.objects.all().count(), 1)
        buff_record = BingoBuff.objects.first()
        self.assertEqual(buff_record.earner_id, "123")
        self.assertGreaterEqual(buff_record.earned_at, initial_earned_at)
        self.assertEqual(buff_record.bingo_count, 12)
        self.assertEqual(buff_record.challenge_count, 25)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBuff"), False)
        self.assertEqual(response.data.get("blackout"), True)

    def test_check_participant_games_view(self):
        # Missing field values throw errors
        response = self.client.post(
            "/season-06/check-participant-games", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-06/check-participant-games",
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

        # TODO: Test the rest... or not
