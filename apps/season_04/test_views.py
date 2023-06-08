from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount


class Season04TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_check_stamps_request_errors(self):
        # Missing field values throw errors
        response = self.client.post("/season-04/check-stamps", {}, format="json")
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
        self.assertIn("funTimerRank", details)
        self.assertEqual(
            details.get("funTimerRank"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("inviteUses", details)
        self.assertEqual(
            details.get("inviteUses"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "funTimerRank": -1,
                "inviteUses": -1,
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
        self.assertIn("funTimerRank", details)
        self.assertEqual(
            details.get("funTimerRank")[0],
            ErrorDetail(
                string="Ensure this value is greater than or equal to 0.",
                code="min_value",
            ),
        )
        self.assertIn("inviteUses", details)
        self.assertEqual(
            details.get("inviteUses")[0],
            ErrorDetail(
                string="Ensure this value is greater than or equal to 0.",
                code="min_value",
            ),
        )

    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_check_stamps_view(self, mock_get_xuid_and_exact_gamertag):
        # Create test data
        mock_get_xuid_and_exact_gamertag.return_value = (4567, "test1234")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="1234", discord_username="TestUsername1234"
        )
        xbox_live_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="testGT1234"
        )
        link = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account=discord_account,
            xbox_live_account=xbox_live_account,
            verified=True,
        )

        # Success - point totals come through for all values
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
                "funTimerRank": 5,
                "inviteUses": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("stampsCompleted"), 2)
        self.assertEqual(response.data.get("scoreChatterbox"), 5)
        self.assertEqual(response.data.get("scoreFuntagious"), 1)
        self.assertEqual(response.data.get("scoreReppingIt"), -1)
        self.assertEqual(response.data.get("scoreFundurance"), -1)
        self.assertEqual(response.data.get("scoreGangsAllHere"), -1)
        self.assertEqual(response.data.get("scoreStackingDubs"), -1)
        self.assertEqual(response.data.get("scoreLicenseToKill"), -1)
        self.assertEqual(response.data.get("scoreAimForTheHead"), -1)
        self.assertEqual(response.data.get("scorePowerTrip"), -1)
        self.assertEqual(response.data.get("scoreBotBullying"), -1)
        self.assertEqual(response.data.get("scoreOneFundo"), -1)
        self.assertEqual(response.data.get("scoreGleeFiddy"), -1)
        self.assertEqual(response.data.get("scoreWellTraveled"), -1)
        self.assertEqual(response.data.get("scoreMoModesMoFun"), -1)
        self.assertEqual(response.data.get("scorePackedHouse"), -1)
        self.assertEqual(response.data.get("completedFinishInFive"), False)
        self.assertEqual(response.data.get("completedVictoryLap"), False)
        self.assertEqual(response.data.get("completedATeam"), False)
        self.assertEqual(response.data.get("completedSneedsSeedGreed"), False)
        self.assertEqual(response.data.get("completedFuckThatGuy"), False)

        # Success - no linked gamertag
        link.delete()
        response = self.client.post(
            "/season-04/check-stamps",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
                "funTimerRank": 5,
                "inviteUses": 1,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("stampsCompleted"), 2)
        self.assertEqual(response.data.get("scoreChatterbox"), 5)
        self.assertEqual(response.data.get("scoreFuntagious"), 1)
        self.assertEqual(response.data.get("scoreReppingIt"), -1)
        self.assertEqual(response.data.get("scoreFundurance"), -1)
        self.assertEqual(response.data.get("scoreGangsAllHere"), -1)
        self.assertEqual(response.data.get("scoreStackingDubs"), -1)
        self.assertEqual(response.data.get("scoreLicenseToKill"), -1)
        self.assertEqual(response.data.get("scoreAimForTheHead"), -1)
        self.assertEqual(response.data.get("scorePowerTrip"), -1)
        self.assertEqual(response.data.get("scoreBotBullying"), -1)
        self.assertEqual(response.data.get("scoreOneFundo"), -1)
        self.assertEqual(response.data.get("scoreGleeFiddy"), -1)
        self.assertEqual(response.data.get("scoreWellTraveled"), -1)
        self.assertEqual(response.data.get("scoreMoModesMoFun"), -1)
        self.assertEqual(response.data.get("scorePackedHouse"), -1)
        self.assertEqual(response.data.get("completedFinishInFive"), False)
        self.assertEqual(response.data.get("completedVictoryLap"), False)
        self.assertEqual(response.data.get("completedATeam"), False)
        self.assertEqual(response.data.get("completedSneedsSeedGreed"), False)
        self.assertEqual(response.data.get("completedFuckThatGuy"), False)
