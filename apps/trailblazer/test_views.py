import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazer.constants import TRAILBLAZER_TITAN_CSR_MINIMUM
from apps.xbox_live.models import XboxLiveAccount


class TrailblazerTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.trailblazer.views.is_scout_qualified")
    @patch("apps.trailblazer.views.is_sherpa_qualified")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_trailblazer_seasonal_role_check_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_is_sherpa_qualified,
        mock_is_scout_qualified,
    ):
        # Missing field values throw errors
        response = self.client.post(
            "/trailblazer/seasonal-role-check", {}, format="json"
        )
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

        # Improperly formatted value throws errors
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
            {"discordUserId": "abc", "discordUsername": "f"},
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

        # Create some test data
        mock_get_xuid_and_exact_gamertag.return_value = (0, "test0")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="0", discord_username="TestUsername01234"
        )
        xbox_live_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="testGT0"
        )
        link = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account=discord_account,
            xbox_live_account=xbox_live_account,
            verified=True,
        )

        # Exception in is_sherpa_qualified throws error
        mock_is_sherpa_qualified.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
            {
                "discordUserId": link.discord_account.discord_id,
                "discordUsername": link.discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer seasonal role check.",
                code="error",
            ),
        )
        mock_is_sherpa_qualified.assert_called_once_with(link.xbox_live_account_id)
        mock_is_sherpa_qualified.side_effect = None
        mock_is_sherpa_qualified.reset_mock()

        # Exception in is_scout_qualified throws error
        mock_is_scout_qualified.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
            {
                "discordUserId": link.discord_account.discord_id,
                "discordUsername": link.discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer seasonal role check.",
                code="error",
            ),
        )
        mock_is_scout_qualified.assert_called_once_with(
            link.discord_account_id, link.xbox_live_account_id
        )
        mock_is_scout_qualified.side_effect = None
        mock_is_sherpa_qualified.reset_mock()
        mock_is_scout_qualified.reset_mock()

        # All permutations of qualification work
        for tuple in [(True, True), (True, False), (False, True), (False, False)]:
            mock_is_sherpa_qualified.return_value = tuple[0]
            mock_is_scout_qualified.return_value = tuple[1]
            response = self.client.post(
                "/trailblazer/seasonal-role-check",
                {
                    "discordUserId": link.discord_account.discord_id,
                    "discordUsername": link.discord_account.discord_username,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data.get("discordUserId"), link.discord_account_id
            )
            self.assertEqual(response.data.get("sherpa"), tuple[0])
            self.assertEqual(response.data.get("scout"), tuple[1])
            mock_is_sherpa_qualified.assert_called_once_with(link.xbox_live_account_id)
            mock_is_scout_qualified.assert_called_once_with(
                link.discord_account_id, link.xbox_live_account_id
            )
            mock_is_sherpa_qualified.reset_mock()
            mock_is_scout_qualified.reset_mock()

        # Deleting the DiscordXboxLiveLink record changes calls to utility methods; Sherpa is always False
        link.delete()
        for tuple in [(True, True), (True, False), (False, True), (False, False)]:
            mock_is_sherpa_qualified.return_value = tuple[0]
            mock_is_scout_qualified.return_value = tuple[1]
            response = self.client.post(
                "/trailblazer/seasonal-role-check",
                {
                    "discordUserId": link.discord_account.discord_id,
                    "discordUsername": link.discord_account.discord_username,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data.get("discordUserId"), link.discord_account_id
            )
            self.assertEqual(
                response.data.get("sherpa"), False
            )  # Should be permanently false
            self.assertEqual(response.data.get("scout"), tuple[1])
            mock_is_sherpa_qualified.assert_not_called()
            mock_is_scout_qualified.assert_called_once_with(
                link.discord_account_id, None
            )
            mock_is_sherpa_qualified.reset_mock()
            mock_is_scout_qualified.reset_mock()

    def test_trailblazer_scout_progress_view_request_errors(self):
        # Missing field values throw errors
        response = self.client.post("/trailblazer/scout-progress", {}, format="json")
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

        # Improperly formatted value throws errors
        response = self.client.post(
            "/trailblazer/scout-progress",
            {"discordUserId": "abc", "discordUsername": "f"},
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

    @patch("apps.trailblazer.views.get_s3_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_s3_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_season_id")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_s3(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s3_discord_earn_dict,
        mock_get_s3_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "3"
        mock_get_current_era.return_value = None

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

        # Exception in get_s3_discord_earn_dict throws error
        mock_get_s3_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s3_discord_earn_dict.side_effect = None
        mock_get_s3_discord_earn_dict.reset_mock()

        # Exception in get_s3_xbox_earn_dict throws error
        mock_get_s3_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s3_xbox_earn_dict.side_effect = None
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_s3_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 150,
                "sharing_is_caring": 50,
                "bookworm": 50,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "online_warrior": 200,
                "hot_streak": 100,
                "oddly_effective": 100,
                "too_stronk": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 750)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsSharingIsCaring"), 50)
        self.assertEqual(response.data.get("pointsBookworm"), 50)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 200)
        self.assertEqual(response.data.get("pointsHotStreak"), 100)
        self.assertEqual(response.data.get("pointsOddlyEffective"), 100)
        self.assertEqual(response.data.get("pointsTooStronk"), 100)
        mock_get_s3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_s3_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 150,
                "sharing_is_caring": 50,
                "bookworm": 50,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "online_warrior": 200,
                "hot_streak": 100,
                "oddly_effective": 100,
                "too_stronk": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 250)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsSharingIsCaring"), 50)
        self.assertEqual(response.data.get("pointsBookworm"), 50)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 0)
        self.assertEqual(response.data.get("pointsHotStreak"), 0)
        self.assertEqual(response.data.get("pointsOddlyEffective"), 0)
        self.assertEqual(response.data.get("pointsTooStronk"), 0)
        mock_get_s3_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_s3_xbox_earn_dict.assert_not_called()
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

    @patch("apps.trailblazer.views.get_s4_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_s4_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_season_id")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_s4(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s4_discord_earn_dict,
        mock_get_s4_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "4"
        mock_get_current_era.return_value = None

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

        # Exception in get_s4_discord_earn_dict throws error
        mock_get_s4_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s4_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s4_discord_earn_dict.side_effect = None
        mock_get_s4_discord_earn_dict.reset_mock()

        # Exception in get_s4_xbox_earn_dict throws error
        mock_get_s4_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s4_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s4_xbox_earn_dict.side_effect = None
        mock_get_s4_discord_earn_dict.reset_mock()
        mock_get_s4_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_s4_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 150,
                "bookworm": 50,
                "film_critic": 100,
            }
        }
        mock_get_s4_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "online_warrior": 200,
                "the_cycle": 100,
                "checkered_flag": 100,
                "them_thar_hills": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 800)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsBookworm"), 50)
        self.assertEqual(response.data.get("pointsFilmCritic"), 100)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 200)
        self.assertEqual(response.data.get("pointsTheCycle"), 100)
        self.assertEqual(response.data.get("pointsCheckeredFlag"), 100)
        self.assertEqual(response.data.get("pointsThemTharHills"), 100)
        mock_get_s4_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s4_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s4_discord_earn_dict.reset_mock()
        mock_get_s4_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_s4_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 150,
                "bookworm": 50,
                "film_critic": 100,
            }
        }
        mock_get_s4_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "online_warrior": 200,
                "the_cycle": 100,
                "checkered_flag": 100,
                "them_thar_hills": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 300)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsBookworm"), 50)
        self.assertEqual(response.data.get("pointsFilmCritic"), 100)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 0)
        self.assertEqual(response.data.get("pointsTheCycle"), 0)
        self.assertEqual(response.data.get("pointsCheckeredFlag"), 0)
        self.assertEqual(response.data.get("pointsThemTharHills"), 0)
        mock_get_s4_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_s4_xbox_earn_dict.assert_not_called()
        mock_get_s4_discord_earn_dict.reset_mock()
        mock_get_s4_xbox_earn_dict.reset_mock()

    @patch("apps.trailblazer.views.get_s5_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_s5_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_season_id")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_s5(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s5_discord_earn_dict,
        mock_get_s5_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "5"
        mock_get_current_era.return_value = None

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

        # Exception in get_s5_discord_earn_dict throws error
        mock_get_s5_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s5_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s5_discord_earn_dict.side_effect = None
        mock_get_s5_discord_earn_dict.reset_mock()

        # Exception in get_s5_xbox_earn_dict throws error
        mock_get_s5_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_s5_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s5_xbox_earn_dict.side_effect = None
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_s5_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 250,
            }
        }
        mock_get_s5_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "online_warrior": 200,
                "heads_or_tails": 150,
                "high_voltage": 100,
                "exterminator": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 800)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 250)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 200)
        self.assertEqual(response.data.get("pointsHeadsOrTails"), 150)
        self.assertEqual(response.data.get("pointsHighVoltage"), 100)
        self.assertEqual(response.data.get("pointsExterminator"), 100)
        mock_get_s5_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s5_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_s5_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 150,
            }
        }
        mock_get_s5_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "online_warrior": 200,
                "heads_or_tails": 150,
                "high_voltage": 100,
                "exterminator": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 150)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsOnlineWarrior"), 0)
        self.assertEqual(response.data.get("pointsHeadsOrTails"), 0)
        self.assertEqual(response.data.get("pointsHighVoltage"), 0)
        self.assertEqual(response.data.get("pointsExterminator"), 0)
        mock_get_s5_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_s5_xbox_earn_dict.assert_not_called()
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

    @patch("apps.trailblazer.views.get_e1_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_e1_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_season_id")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_e1(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e1_discord_earn_dict,
        mock_get_e1_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = None
        mock_get_current_era.return_value = 1

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

        # Exception in get_e1_discord_earn_dict throws error
        mock_get_e1_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_e1_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e1_discord_earn_dict.side_effect = None
        mock_get_e1_discord_earn_dict.reset_mock()

        # Exception in get_e1_xbox_earn_dict throws error
        mock_get_e1_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_e1_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e1_xbox_earn_dict.side_effect = None
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_e1_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 250,
            }
        }
        mock_get_e1_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "csr_go_up": 200,
                "play_to_slay": 150,
                "mean_streets": 100,
                "hot_streak": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 800)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 250)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 200)
        self.assertEqual(response.data.get("pointsPlayToSlay"), 150)
        self.assertEqual(response.data.get("pointsMeanStreets"), 100)
        self.assertEqual(response.data.get("pointsHotStreak"), 100)
        mock_get_e1_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e1_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_e1_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 150,
            }
        }
        mock_get_e1_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "csr_go_up": 200,
                "play_to_slay": 150,
                "mean_streets": 100,
                "hot_streak": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 150)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 0)
        self.assertEqual(response.data.get("pointsPlayToSlay"), 0)
        self.assertEqual(response.data.get("pointsMeanStreets"), 0)
        self.assertEqual(response.data.get("pointsHotStreak"), 0)
        mock_get_e1_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_e1_xbox_earn_dict.assert_not_called()
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

    @patch("apps.trailblazer.views.get_e2_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_e2_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_season_id")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_e2(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e2_discord_earn_dict,
        mock_get_e2_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = None
        mock_get_current_era.return_value = 2

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

        # Exception in get_e2_discord_earn_dict throws error
        mock_get_e2_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_e2_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e2_discord_earn_dict.side_effect = None
        mock_get_e2_discord_earn_dict.reset_mock()

        # Exception in get_e2_xbox_earn_dict throws error
        mock_get_e2_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Scout progress check.",
                code="error",
            ),
        )
        mock_get_e2_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e2_xbox_earn_dict.side_effect = None
        mock_get_e2_discord_earn_dict.reset_mock()
        mock_get_e2_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_e2_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 250,
            }
        }
        mock_get_e2_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "csr_go_up": 200,
                "too_stronk": 150,
                "scoreboard": 100,
                "the_cycle": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 800)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 250)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 200)
        self.assertEqual(response.data.get("pointsTooStronk"), 150)
        self.assertEqual(response.data.get("pointsScoreboard"), 100)
        self.assertEqual(response.data.get("pointsTheCycle"), 100)
        mock_get_e2_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e2_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e2_discord_earn_dict.reset_mock()
        mock_get_e2_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_e2_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 150,
            }
        }
        mock_get_e2_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "csr_go_up": 200,
                "too_stronk": 150,
                "scoreboard": 100,
                "the_cycle": 100,
            }
        }
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 150)
        self.assertEqual(response.data.get("pointsChurchOfTheCrab"), 150)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 0)
        self.assertEqual(response.data.get("pointsTooStronk"), 0)
        self.assertEqual(response.data.get("pointsScoreboard"), 0)
        self.assertEqual(response.data.get("pointsTheCycle"), 0)
        mock_get_e2_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_e2_xbox_earn_dict.assert_not_called()
        mock_get_e2_discord_earn_dict.reset_mock()
        mock_get_e2_xbox_earn_dict.reset_mock()

    @patch("apps.trailblazer.views.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_trailblazer_titan_check_view(
        self, mock_get_xuid_and_exact_gamertag, mock_get_csrs
    ):
        # Missing field values throw errors
        response = self.client.post("/trailblazer/titan-check", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("playlistId", details)
        self.assertEqual(
            details.get("playlistId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/trailblazer/titan-check",
            {"discordUserIds": ["abc"], "playlistId": 1},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds")[0],
            [
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                )
            ],
        )
        self.assertIn("playlistId", details)
        self.assertEqual(
            details.get("playlistId"),
            [
                ErrorDetail(
                    string="Only a valid UUID string is allowed.", code="invalid"
                )
            ],
        )

        # Create some test data
        test_playlist_id = str(uuid.uuid4())
        links = []
        for i in range(10):
            mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
            discord_account = DiscordAccount.objects.create(
                creator=self.user,
                discord_id=str(i),
                discord_username=f"TestUsername{i}",
            )
            xbox_live_account = XboxLiveAccount.objects.create(
                creator=self.user, gamertag=f"testGT{i}"
            )
            links.append(
                DiscordXboxLiveLink.objects.create(
                    creator=self.user,
                    discord_account=discord_account,
                    xbox_live_account=xbox_live_account,
                    verified=True,
                )
            )

        def titan_check_dict(discord_id, csr):
            return {
                "currentCSR": csr,
                "discordUserId": discord_id,
            }

        # Exception in get_csrs throws error
        mock_get_csrs.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/titan-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                ],
                "playlistId": test_playlist_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Trailblazer Titan check.", code="error"
            ),
        )
        mock_get_csrs.assert_called_once_with(
            [
                links[0].xbox_live_account_id,
                links[1].xbox_live_account_id,
                links[2].xbox_live_account_id,
            ],
            test_playlist_id,
        )
        mock_get_csrs.reset_mock()

        # Success - all accounts have ranks
        mock_get_csrs.return_value = {
            "csrs": {
                links[0].xbox_live_account_id: {
                    "current_csr": 1800,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": 1700,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 1600,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": 1599,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": 1500,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": 1400,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 1300,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": 1200,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 1000,
                },
                links[9].xbox_live_account_id: {
                    "current_csr": 900,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/trailblazer/titan-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                    links[3].discord_account_id,
                    links[4].discord_account_id,
                    links[5].discord_account_id,
                    links[6].discord_account_id,
                    links[7].discord_account_id,
                    links[8].discord_account_id,
                    links[9].discord_account_id,
                ],
                "playlistId": test_playlist_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.data.get("yes"),
            [
                titan_check_dict(links[0].discord_account_id, 1800),
                titan_check_dict(links[1].discord_account_id, 1700),
                titan_check_dict(links[2].discord_account_id, 1600),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(links[3].discord_account_id, 1599),
                titan_check_dict(links[4].discord_account_id, 1500),
                titan_check_dict(links[5].discord_account_id, 1400),
                titan_check_dict(links[6].discord_account_id, 1300),
                titan_check_dict(links[7].discord_account_id, 1200),
                titan_check_dict(links[8].discord_account_id, 1000),
                titan_check_dict(links[9].discord_account_id, 900),
            ],
        )
        self.assertEqual(
            response.data.get("thresholdCSR"), TRAILBLAZER_TITAN_CSR_MINIMUM
        )
        mock_get_csrs.assert_called_once_with(
            [
                links[0].xbox_live_account_id,
                links[1].xbox_live_account_id,
                links[2].xbox_live_account_id,
                links[3].xbox_live_account_id,
                links[4].xbox_live_account_id,
                links[5].xbox_live_account_id,
                links[6].xbox_live_account_id,
                links[7].xbox_live_account_id,
                links[8].xbox_live_account_id,
                links[9].xbox_live_account_id,
            ],
            test_playlist_id,
        )
        mock_get_csrs.reset_mock()

        # Success - some accounts have ranks and some are unranked
        mock_get_csrs.return_value = {
            "csrs": {
                links[0].xbox_live_account_id: {
                    "current_csr": 1600,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": 1600,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 1500,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": 1500,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 800,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 1650,
                },
                links[9].xbox_live_account_id: {
                    "current_csr": None,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/trailblazer/titan-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                    links[3].discord_account_id,
                    links[4].discord_account_id,
                    links[5].discord_account_id,
                    links[6].discord_account_id,
                    links[7].discord_account_id,
                    links[8].discord_account_id,
                    links[9].discord_account_id,
                ],
                "playlistId": test_playlist_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.data.get("yes"),
            [
                titan_check_dict(links[0].discord_account_id, 1600),
                titan_check_dict(links[1].discord_account_id, 1600),
                titan_check_dict(links[8].discord_account_id, 1650),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(links[2].discord_account_id, 1500),
                titan_check_dict(links[3].discord_account_id, 1500),
                titan_check_dict(links[4].discord_account_id, None),
                titan_check_dict(links[5].discord_account_id, None),
                titan_check_dict(links[6].discord_account_id, 800),
                titan_check_dict(links[7].discord_account_id, None),
                titan_check_dict(links[9].discord_account_id, None),
            ],
        )
        self.assertEqual(
            response.data.get("thresholdCSR"), TRAILBLAZER_TITAN_CSR_MINIMUM
        )
        mock_get_csrs.assert_called_once_with(
            [
                links[0].xbox_live_account_id,
                links[1].xbox_live_account_id,
                links[2].xbox_live_account_id,
                links[3].xbox_live_account_id,
                links[4].xbox_live_account_id,
                links[5].xbox_live_account_id,
                links[6].xbox_live_account_id,
                links[7].xbox_live_account_id,
                links[8].xbox_live_account_id,
                links[9].xbox_live_account_id,
            ],
            test_playlist_id,
        )
        mock_get_csrs.reset_mock()

        # Success - some rank data missing from CSR result
        mock_get_csrs.return_value = {
            "csrs": {
                links[0].xbox_live_account_id: {
                    "current_csr": 1800,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 1600,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": 1500,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 1200,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 700,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/trailblazer/titan-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                    links[3].discord_account_id,
                    links[4].discord_account_id,
                    links[5].discord_account_id,
                    links[6].discord_account_id,
                    links[7].discord_account_id,
                    links[8].discord_account_id,
                    links[9].discord_account_id,
                ],
                "playlistId": test_playlist_id,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            response.data.get("yes"),
            [
                titan_check_dict(links[0].discord_account_id, 1800),
                titan_check_dict(links[2].discord_account_id, 1600),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(links[1].discord_account_id, None),
                titan_check_dict(links[3].discord_account_id, None),
                titan_check_dict(links[4].discord_account_id, 1500),
                titan_check_dict(links[5].discord_account_id, None),
                titan_check_dict(links[6].discord_account_id, 1200),
                titan_check_dict(links[7].discord_account_id, None),
                titan_check_dict(links[8].discord_account_id, 700),
                titan_check_dict(links[9].discord_account_id, None),
            ],
        )
        self.assertEqual(
            response.data.get("thresholdCSR"), TRAILBLAZER_TITAN_CSR_MINIMUM
        )
        mock_get_csrs.assert_called_once_with(
            [
                links[0].xbox_live_account_id,
                links[1].xbox_live_account_id,
                links[2].xbox_live_account_id,
                links[3].xbox_live_account_id,
                links[4].xbox_live_account_id,
                links[5].xbox_live_account_id,
                links[6].xbox_live_account_id,
                links[7].xbox_live_account_id,
                links[8].xbox_live_account_id,
                links[9].xbox_live_account_id,
            ],
            test_playlist_id,
        )
        mock_get_csrs.reset_mock()
