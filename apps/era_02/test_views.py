import datetime

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.era_02.models import MVT


class Era02TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_save_mvt_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-02/save-mvt", {}, format="json")
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
        self.assertIn("mvtPoints", details)
        self.assertEqual(
            details.get("mvtPoints"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "mvtPoints": "not_an_int",
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
        self.assertIn("mvtPoints", details)
        self.assertEqual(
            details.get("mvtPoints")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New MVT
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "mvtPoints": 100,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, now_before_post)
        self.assertEqual(mvt_record.mvt_points, 100)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), True)
        self.assertEqual(response.data.get("maxed"), False)
        initial_earned_at = mvt_record.earned_at

        # Existing MVT, MVT points update
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "mvtPoints": 117,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, initial_earned_at)
        self.assertEqual(mvt_record.mvt_points, 117)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), False)
        self.assertEqual(response.data.get("maxed"), False)

        # Existing MVT, maxed
        response = self.client.post(
            "/era-02/save-mvt",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "mvtPoints": 250,
            },
            format="json",
        )
        self.assertEqual(MVT.objects.all().count(), 1)
        mvt_record = MVT.objects.first()
        self.assertEqual(mvt_record.earner_id, "123")
        self.assertGreaterEqual(mvt_record.earned_at, initial_earned_at)
        self.assertEqual(mvt_record.mvt_points, 250)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMVT"), False)
        self.assertEqual(response.data.get("maxed"), True)

    def test_check_player_games_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-02/check-player-games", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-02/check-player-games",
            {
                "discordUserId": ["abc"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Not a valid string.", code="invalid"),
        )

        # TODO: Test the rest... or not
