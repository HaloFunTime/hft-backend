import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
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
                creator=self.user, discord_id=str(i), discord_tag=f"TestTag{i}#1234"
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
