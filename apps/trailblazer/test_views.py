from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
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
