from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount


class PathfinderTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.pathfinder.views.get_dynamo_qualified")
    @patch("apps.pathfinder.views.get_illuminated_qualified")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_seasonal_role_check_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_illuminated_qualified,
        mock_get_dynamo_qualified,
    ):
        # Missing field values throw errors
        response = self.client.post(
            "/pathfinder/seasonal-role-check", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted value throws errors
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {"discordUserIds": ["abc"]},
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

        # Create some test data
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

        # Exception in get_illuminated_qualified throws error
        mock_get_illuminated_qualified.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Pathfinder seasonal role check.",
                code="error",
            ),
        )
        mock_get_illuminated_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
            ],
        )
        mock_get_illuminated_qualified.side_effect = None
        mock_get_illuminated_qualified.reset_mock()

        # Exception in get_dynamo_qualified throws error
        mock_get_dynamo_qualified.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {
                "discordUserIds": [
                    links[0].discord_account_id,
                    links[1].discord_account_id,
                    links[2].discord_account_id,
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Pathfinder seasonal role check.",
                code="error",
            ),
        )
        mock_get_dynamo_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
            ],
        )
        mock_get_dynamo_qualified.side_effect = None
        mock_get_illuminated_qualified.reset_mock()
        mock_get_dynamo_qualified.reset_mock()

        # Success - some illuminateds and some dynamos
        mock_get_illuminated_qualified.return_value = [
            links[0].discord_account_id,
            links[2].discord_account_id,
            links[4].discord_account_id,
            links[6].discord_account_id,
            links[8].discord_account_id,
        ]
        mock_get_dynamo_qualified.return_value = [
            links[1].discord_account_id,
            links[3].discord_account_id,
            links[5].discord_account_id,
            links[7].discord_account_id,
            links[9].discord_account_id,
        ]
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
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
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("illuminated"),
            [
                links[0].discord_account_id,
                links[2].discord_account_id,
                links[4].discord_account_id,
                links[6].discord_account_id,
                links[8].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("dynamo"),
            [
                links[1].discord_account_id,
                links[3].discord_account_id,
                links[5].discord_account_id,
                links[7].discord_account_id,
                links[9].discord_account_id,
            ],
        )
        mock_get_illuminated_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
                links[3],
                links[4],
                links[5],
                links[6],
                links[7],
                links[8],
                links[9],
            ]
        )
        mock_get_dynamo_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
                links[3],
                links[4],
                links[5],
                links[6],
                links[7],
                links[8],
                links[9],
            ]
        )
        mock_get_illuminated_qualified.reset_mock()
        mock_get_dynamo_qualified.reset_mock()

        # Success - no illuminateds or dynamos
        mock_get_illuminated_qualified.return_value = []
        mock_get_dynamo_qualified.return_value = []
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
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
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("illuminated"), [])
        self.assertEqual(response.data.get("dynamo"), [])
        mock_get_illuminated_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
                links[3],
                links[4],
                links[5],
                links[6],
                links[7],
                links[8],
                links[9],
            ]
        )
        mock_get_dynamo_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
                links[3],
                links[4],
                links[5],
                links[6],
                links[7],
                links[8],
                links[9],
            ]
        )
        mock_get_illuminated_qualified.reset_mock()
        mock_get_dynamo_qualified.reset_mock()
