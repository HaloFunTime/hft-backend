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

    @patch("apps.trailblazer.views.get_e1_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_e1_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_e1(
        self,
        mock_get_current_era,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e1_discord_earn_dict,
        mock_get_e1_xbox_earn_dict,
    ):
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
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_e2(
        self,
        mock_get_current_era,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e2_discord_earn_dict,
        mock_get_e2_xbox_earn_dict,
    ):
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

    @patch("apps.trailblazer.views.get_e3_xbox_earn_dict")
    @patch("apps.trailblazer.views.get_e3_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.trailblazer.views.get_current_era")
    def test_trailblazer_scout_progress_view_e3(
        self,
        mock_get_current_era,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e3_discord_earn_dict,
        mock_get_e3_xbox_earn_dict,
    ):
        mock_get_current_era.return_value = 3

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

        # Exception in get_e3_discord_earn_dict throws error
        mock_get_e3_discord_earn_dict.side_effect = Exception()
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
        mock_get_e3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e3_discord_earn_dict.side_effect = None
        mock_get_e3_discord_earn_dict.reset_mock()

        # Exception in get_e3_xbox_earn_dict throws error
        mock_get_e3_xbox_earn_dict.side_effect = Exception()
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
        mock_get_e3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e3_xbox_earn_dict.side_effect = None
        mock_get_e3_discord_earn_dict.reset_mock()
        mock_get_e3_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_e3_discord_earn_dict.return_value = {link.discord_account_id: {}}
        mock_get_e3_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "csr_go_up": 300,
                "bomb_dot_com": 100,
                "oddly_effective": 100,
                "its_the_age": 100,
                "overkill": 100,
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
        self.assertEqual(response.data.get("totalPoints"), 700)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 300)
        self.assertEqual(response.data.get("pointsBombDotCom"), 100)
        self.assertEqual(response.data.get("pointsOddlyEffective"), 100)
        self.assertEqual(response.data.get("pointsItsTheAge"), 100)
        self.assertEqual(response.data.get("pointsOverkill"), 100)
        mock_get_e3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e3_discord_earn_dict.reset_mock()
        mock_get_e3_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_e3_discord_earn_dict.return_value = {discord_account.discord_id: {}}
        mock_get_e3_xbox_earn_dict.return_value = {
            xbox_live_account.xuid: {
                "csr_go_up": 300,
                "bomb_dot_com": 100,
                "oddly_effective": 100,
                "its_the_age": 100,
                "overkill": 100,
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
        self.assertEqual(response.data.get("totalPoints"), 0)
        self.assertEqual(response.data.get("pointsCSRGoUp"), 0)
        self.assertEqual(response.data.get("pointsBombDotCom"), 0)
        self.assertEqual(response.data.get("pointsOddlyEffective"), 0)
        self.assertEqual(response.data.get("pointsItsTheAge"), 0)
        self.assertEqual(response.data.get("pointsOverkill"), 0)
        mock_get_e3_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_e3_xbox_earn_dict.assert_not_called()
        mock_get_e3_discord_earn_dict.reset_mock()
        mock_get_e3_xbox_earn_dict.reset_mock()

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
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM + 100,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM + 1,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 1,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 100,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 200,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 300,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 400,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 500,
                },
                links[9].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 600,
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
                titan_check_dict(
                    links[0].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM + 100
                ),
                titan_check_dict(
                    links[1].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM + 1
                ),
                titan_check_dict(
                    links[2].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM
                ),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(
                    links[3].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 1
                ),
                titan_check_dict(
                    links[4].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 100
                ),
                titan_check_dict(
                    links[5].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 200
                ),
                titan_check_dict(
                    links[6].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 300
                ),
                titan_check_dict(
                    links[7].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 400
                ),
                titan_check_dict(
                    links[8].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 500
                ),
                titan_check_dict(
                    links[9].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 600
                ),
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
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 100,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 100,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 700,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": None,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM + 50,
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
                titan_check_dict(
                    links[0].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM
                ),
                titan_check_dict(
                    links[1].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM
                ),
                titan_check_dict(
                    links[8].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM + 50
                ),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(
                    links[2].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 100
                ),
                titan_check_dict(
                    links[3].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 100
                ),
                titan_check_dict(links[4].discord_account_id, None),
                titan_check_dict(links[5].discord_account_id, None),
                titan_check_dict(
                    links[6].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 700
                ),
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
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM + 100,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 100,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 400,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": TRAILBLAZER_TITAN_CSR_MINIMUM - 800,
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
                titan_check_dict(
                    links[0].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM + 100
                ),
                titan_check_dict(
                    links[2].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM
                ),
            ],
        )
        self.assertCountEqual(
            response.data.get("no"),
            [
                titan_check_dict(links[1].discord_account_id, None),
                titan_check_dict(links[3].discord_account_id, None),
                titan_check_dict(
                    links[4].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 100
                ),
                titan_check_dict(links[5].discord_account_id, None),
                titan_check_dict(
                    links[6].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 400
                ),
                titan_check_dict(links[7].discord_account_id, None),
                titan_check_dict(
                    links[8].discord_account_id, TRAILBLAZER_TITAN_CSR_MINIMUM - 800
                ),
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
