import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import (
    DiscordAccount,
    DiscordLFGChannelHelpPrompt,
    DiscordLFGThreadHelpPrompt,
)
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount


class DiscordTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.discord.views.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_csr_snapshot_view(self, mock_get_xuid_and_exact_gamertag, mock_get_csrs):
        # Missing field values throw errors
        response = self.client.post("/discord/csr-snapshot", {}, format="json")
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
            "/discord/csr-snapshot",
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

        # Exception in get_csrs throws error
        mock_get_csrs.side_effect = Exception()
        response = self.client.post(
            "/discord/csr-snapshot",
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
            ErrorDetail(string="Error attempting the CSR snapshot.", code="error"),
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
                    "current_csr": 0,
                    "current_reset_max_csr": 1,
                    "all_time_max_csr": 2,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": 3,
                    "current_reset_max_csr": 4,
                    "all_time_max_csr": 5,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 6,
                    "current_reset_max_csr": 7,
                    "all_time_max_csr": 8,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": 9,
                    "current_reset_max_csr": 10,
                    "all_time_max_csr": 11,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": 12,
                    "current_reset_max_csr": 13,
                    "all_time_max_csr": 14,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": 15,
                    "current_reset_max_csr": 16,
                    "all_time_max_csr": 17,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 18,
                    "current_reset_max_csr": 19,
                    "all_time_max_csr": 20,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": 21,
                    "current_reset_max_csr": 22,
                    "all_time_max_csr": 23,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 24,
                    "current_reset_max_csr": 25,
                    "all_time_max_csr": 26,
                },
                links[9].xbox_live_account_id: {
                    "current_csr": 27,
                    "current_reset_max_csr": 28,
                    "all_time_max_csr": 29,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/csr-snapshot",
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
        players = response.data.get("players")
        self.assertIsNotNone(players)
        self.assertEqual(len(players), 10)
        for i in range(10):
            self.assertEqual(players[i].get("discordUserId"), str(i))
            self.assertEqual(players[i].get("currentCSR"), i * 3)
            self.assertEqual(players[i].get("currentResetMaxCSR"), i * 3 + 1)
            self.assertEqual(players[i].get("allTimeMaxCSR"), i * 3 + 2)
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
                    "current_csr": 0,
                    "current_reset_max_csr": 1,
                    "all_time_max_csr": 2,
                },
                links[1].xbox_live_account_id: {
                    "current_csr": -1,
                    "current_reset_max_csr": -1,
                    "all_time_max_csr": 5,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 6,
                    "current_reset_max_csr": 7,
                    "all_time_max_csr": 8,
                },
                links[3].xbox_live_account_id: {
                    "current_csr": -1,
                    "current_reset_max_csr": -1,
                    "all_time_max_csr": 11,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": 12,
                    "current_reset_max_csr": 13,
                    "all_time_max_csr": 14,
                },
                links[5].xbox_live_account_id: {
                    "current_csr": -1,
                    "current_reset_max_csr": -1,
                    "all_time_max_csr": 17,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 18,
                    "current_reset_max_csr": 19,
                    "all_time_max_csr": 20,
                },
                links[7].xbox_live_account_id: {
                    "current_csr": -1,
                    "current_reset_max_csr": -1,
                    "all_time_max_csr": -1,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 24,
                    "current_reset_max_csr": 25,
                    "all_time_max_csr": 26,
                },
                links[9].xbox_live_account_id: {
                    "current_csr": -1,
                    "current_reset_max_csr": -1,
                    "all_time_max_csr": -1,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/csr-snapshot",
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
        players = response.data.get("players")
        self.assertIsNotNone(players)
        self.assertEqual(len(players), 10)
        for i in range(10):
            self.assertEqual(players[i].get("discordUserId"), str(i))
            self.assertEqual(players[i].get("currentCSR"), -1 if i % 2 == 1 else i * 3)
            self.assertEqual(
                players[i].get("currentResetMaxCSR"), -1 if i % 2 == 1 else i * 3 + 1
            )
            self.assertEqual(
                players[i].get("allTimeMaxCSR"),
                -1 if i == 7 else -1 if i == 9 else i * 3 + 2,
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
                    "current_csr": 0,
                    "current_reset_max_csr": 1,
                    "all_time_max_csr": 2,
                },
                links[2].xbox_live_account_id: {
                    "current_csr": 6,
                    "current_reset_max_csr": 7,
                    "all_time_max_csr": 8,
                },
                links[4].xbox_live_account_id: {
                    "current_csr": 12,
                    "current_reset_max_csr": 13,
                    "all_time_max_csr": 14,
                },
                links[6].xbox_live_account_id: {
                    "current_csr": 18,
                    "current_reset_max_csr": 19,
                    "all_time_max_csr": 20,
                },
                links[8].xbox_live_account_id: {
                    "current_csr": 24,
                    "current_reset_max_csr": 25,
                    "all_time_max_csr": 26,
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/csr-snapshot",
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
        players = response.data.get("players")
        self.assertIsNotNone(players)
        self.assertEqual(len(players), 5)
        for i in range(5):
            self.assertEqual(players[i].get("discordUserId"), str(i * 2))
            self.assertEqual(players[i].get("currentCSR"), i * 6)
            self.assertEqual(players[i].get("currentResetMaxCSR"), i * 6 + 1)
            self.assertEqual(players[i].get("allTimeMaxCSR"), i * 6 + 2)
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

    def test_lfg_channel_help_prompt_view(self):
        # Missing field values throw errors
        response = self.client.post(
            "/discord/lfg-channel-help-prompt", {}, format="json"
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
        self.assertIn("lfgChannelId", details)
        self.assertEqual(
            details.get("lfgChannelId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("lfgChannelName", details)
        self.assertEqual(
            details.get("lfgChannelName"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/discord/lfg-channel-help-prompt",
            {
                "discordUserId": "abc",
                "discordUsername": "a",
                "lfgChannelId": "def",
                "lfgChannelName": "",
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
                string="Ensure this field has at least 2 characters.", code="min_length"
            ),
        )
        self.assertIn("lfgChannelId", details)
        self.assertEqual(
            details.get("lfgChannelId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("lfgChannelName", details)
        self.assertEqual(
            details.get("lfgChannelName")[0],
            ErrorDetail(string="This field may not be blank.", code="blank"),
        )

        # First call to endpoint with same data
        response = self.client.post(
            "/discord/lfg-channel-help-prompt",
            {
                "discordUserId": "123456789",
                "discordUsername": "Test123",
                "lfgChannelId": "987654321",
                "lfgChannelName": "Test LFG Channel",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertTrue(response.data.get("new"))
        self.assertEqual(DiscordLFGChannelHelpPrompt.objects.count(), 1)
        prompt = DiscordLFGChannelHelpPrompt.objects.first()
        self.assertEqual(prompt.help_receiver_discord.discord_id, "123456789")
        self.assertEqual(prompt.help_receiver_discord.discord_username, "Test123")
        self.assertEqual(prompt.lfg_channel_id, "987654321")
        self.assertEqual(prompt.lfg_channel_name, "Test LFG Channel")

        # Second call to endpoint with same data
        response = self.client.post(
            "/discord/lfg-channel-help-prompt",
            {
                "discordUserId": "123456789",
                "discordUsername": "Test123",
                "lfgChannelId": "987654321",
                "lfgChannelName": "Test LFG Channel",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertFalse(response.data.get("new"))
        self.assertEqual(DiscordLFGChannelHelpPrompt.objects.count(), 1)

    def test_lfg_thread_help_prompt_view(self):
        # Missing field values throw errors
        response = self.client.post(
            "/discord/lfg-thread-help-prompt", {}, format="json"
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
        self.assertIn("lfgThreadId", details)
        self.assertEqual(
            details.get("lfgThreadId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("lfgThreadName", details)
        self.assertEqual(
            details.get("lfgThreadName"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/discord/lfg-thread-help-prompt",
            {
                "discordUserId": "abc",
                "discordUsername": "a",
                "lfgThreadId": "def",
                "lfgThreadName": "",
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
                string="Ensure this field has at least 2 characters.", code="min_length"
            ),
        )
        self.assertIn("lfgThreadId", details)
        self.assertEqual(
            details.get("lfgThreadId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("lfgThreadName", details)
        self.assertEqual(
            details.get("lfgThreadName")[0],
            ErrorDetail(string="This field may not be blank.", code="blank"),
        )

        # First call to endpoint with same data
        response = self.client.post(
            "/discord/lfg-thread-help-prompt",
            {
                "discordUserId": "123456789",
                "discordUsername": "Test123",
                "lfgThreadId": "987654321",
                "lfgThreadName": "Test LFG Thread",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertTrue(response.data.get("new"))
        self.assertEqual(DiscordLFGThreadHelpPrompt.objects.count(), 1)
        prompt = DiscordLFGThreadHelpPrompt.objects.first()
        self.assertEqual(prompt.help_receiver_discord.discord_id, "123456789")
        self.assertEqual(prompt.help_receiver_discord.discord_username, "Test123")
        self.assertEqual(prompt.lfg_thread_id, "987654321")
        self.assertEqual(prompt.lfg_thread_name, "Test LFG Thread")

        # Second call to endpoint with same data
        response = self.client.post(
            "/discord/lfg-thread-help-prompt",
            {
                "discordUserId": "123456789",
                "discordUsername": "Test123",
                "lfgThreadId": "987654321",
                "lfgThreadName": "Test LFG Thread",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertFalse(response.data.get("new"))
        self.assertEqual(DiscordLFGThreadHelpPrompt.objects.count(), 1)

    @patch("apps.discord.views.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_ranked_role_check_view(
        self, mock_get_xuid_and_exact_gamertag, mock_get_csrs
    ):
        # Missing field values throw errors
        response = self.client.post("/discord/ranked-role-check", {}, format="json")
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
            "/discord/ranked-role-check",
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

        # Exception in get_csrs throws error
        mock_get_csrs.side_effect = Exception()
        response = self.client.post(
            "/discord/ranked-role-check",
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
            ErrorDetail(string="Error attempting the ranked role check.", code="error"),
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
                    "current_reset_max_tier": "Onyx",
                },
                links[1].xbox_live_account_id: {
                    "current_reset_max_tier": "Diamond",
                },
                links[2].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
                links[3].xbox_live_account_id: {
                    "current_reset_max_tier": "Gold",
                },
                links[4].xbox_live_account_id: {
                    "current_reset_max_tier": "Silver",
                },
                links[5].xbox_live_account_id: {
                    "current_reset_max_tier": "Bronze",
                },
                links[6].xbox_live_account_id: {
                    "current_reset_max_tier": "Onyx",
                },
                links[7].xbox_live_account_id: {
                    "current_reset_max_tier": "Diamond",
                },
                links[8].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
                links[9].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/ranked-role-check",
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
        self.assertEqual(
            response.data.get("onyx"),
            [links[0].discord_account_id, links[6].discord_account_id],
        )
        self.assertEqual(
            response.data.get("diamond"),
            [
                links[1].discord_account_id,
                links[7].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("platinum"),
            [
                links[2].discord_account_id,
                links[8].discord_account_id,
                links[9].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("gold"),
            [
                links[3].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("silver"),
            [
                links[4].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("bronze"),
            [
                links[5].discord_account_id,
            ],
        )
        self.assertEqual(response.data.get("unranked"), [])
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
                    "current_reset_max_tier": "Onyx",
                },
                links[1].xbox_live_account_id: {
                    "current_reset_max_tier": "Diamond",
                },
                links[2].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
                links[3].xbox_live_account_id: {
                    "current_reset_max_tier": "Gold",
                },
                links[4].xbox_live_account_id: {
                    "current_reset_max_tier": "",
                },
                links[5].xbox_live_account_id: {
                    "current_reset_max_tier": "",
                },
                links[6].xbox_live_account_id: {
                    "current_reset_max_tier": "Onyx",
                },
                links[7].xbox_live_account_id: {
                    "current_reset_max_tier": "",
                },
                links[8].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
                links[9].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/ranked-role-check",
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
        self.assertEqual(
            response.data.get("onyx"),
            [links[0].discord_account_id, links[6].discord_account_id],
        )
        self.assertEqual(response.data.get("diamond"), [links[1].discord_account_id])
        self.assertEqual(
            response.data.get("platinum"),
            [
                links[2].discord_account_id,
                links[8].discord_account_id,
                links[9].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("gold"),
            [
                links[3].discord_account_id,
            ],
        )
        self.assertEqual(response.data.get("silver"), [])
        self.assertEqual(response.data.get("bronze"), [])
        self.assertEqual(
            response.data.get("unranked"),
            [
                links[4].discord_account_id,
                links[5].discord_account_id,
                links[7].discord_account_id,
            ],
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
                    "current_reset_max_tier": "Onyx",
                },
                links[2].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
                links[4].xbox_live_account_id: {
                    "current_reset_max_tier": "Silver",
                },
                links[6].xbox_live_account_id: {
                    "current_reset_max_tier": "Onyx",
                },
                links[8].xbox_live_account_id: {
                    "current_reset_max_tier": "Platinum",
                },
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.post(
            "/discord/ranked-role-check",
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
        self.assertEqual(
            response.data.get("onyx"),
            [links[0].discord_account_id, links[6].discord_account_id],
        )
        self.assertEqual(response.data.get("diamond"), [])
        self.assertEqual(
            response.data.get("platinum"),
            [
                links[2].discord_account_id,
                links[8].discord_account_id,
            ],
        )
        self.assertEqual(response.data.get("gold"), [])
        self.assertEqual(
            response.data.get("silver"),
            [
                links[4].discord_account_id,
            ],
        )
        self.assertEqual(response.data.get("bronze"), [])
        self.assertEqual(response.data.get("unranked"), [])
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
