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

    @patch("apps.trailblazer.views.get_scout_qualified")
    @patch("apps.trailblazer.views.get_sherpa_qualified")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_trailblazer_seasonal_role_check_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_sherpa_qualified,
        mock_get_scout_qualified,
    ):
        # Missing field values throw errors
        response = self.client.post(
            "/trailblazer/seasonal-role-check", {}, format="json"
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
            "/trailblazer/seasonal-role-check",
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

        # Exception in get_sherpa_qualified throws error
        mock_get_sherpa_qualified.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
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
                string="Error attempting the Trailblazer seasonal role check.",
                code="error",
            ),
        )
        mock_get_sherpa_qualified.assert_called_once_with(
            [
                links[0],
                links[1],
                links[2],
            ],
        )
        mock_get_sherpa_qualified.side_effect = None
        mock_get_sherpa_qualified.reset_mock()

        # Exception in get_scout_qualified throws error
        mock_get_scout_qualified.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
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
                string="Error attempting the Trailblazer seasonal role check.",
                code="error",
            ),
        )
        mock_get_scout_qualified.assert_called_once_with(
            [
                links[0].discord_account_id,
                links[1].discord_account_id,
                links[2].discord_account_id,
            ],
            [
                links[0],
                links[1],
                links[2],
            ],
        )
        mock_get_scout_qualified.side_effect = None
        mock_get_sherpa_qualified.reset_mock()
        mock_get_scout_qualified.reset_mock()

        # Success - some Sherpas and some Scouts
        mock_get_sherpa_qualified.return_value = [
            links[0].discord_account_id,
            links[2].discord_account_id,
            links[4].discord_account_id,
            links[6].discord_account_id,
            links[8].discord_account_id,
        ]
        mock_get_scout_qualified.return_value = [
            links[1].discord_account_id,
            links[3].discord_account_id,
            links[5].discord_account_id,
            links[7].discord_account_id,
            links[9].discord_account_id,
        ]
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
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
            response.data.get("sherpa"),
            [
                links[0].discord_account_id,
                links[2].discord_account_id,
                links[4].discord_account_id,
                links[6].discord_account_id,
                links[8].discord_account_id,
            ],
        )
        self.assertEqual(
            response.data.get("scout"),
            [
                links[1].discord_account_id,
                links[3].discord_account_id,
                links[5].discord_account_id,
                links[7].discord_account_id,
                links[9].discord_account_id,
            ],
        )
        mock_get_sherpa_qualified.assert_called_once_with(
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
        mock_get_scout_qualified.assert_called_once_with(
            [
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
            ],
        )
        mock_get_sherpa_qualified.reset_mock()
        mock_get_scout_qualified.reset_mock()

        # Success - no sherpas or scouts
        mock_get_sherpa_qualified.return_value = []
        mock_get_scout_qualified.return_value = []
        response = self.client.post(
            "/trailblazer/seasonal-role-check",
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
        self.assertEqual(response.data.get("sherpa"), [])
        self.assertEqual(response.data.get("scout"), [])
        mock_get_sherpa_qualified.assert_called_once_with(
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
        mock_get_scout_qualified.assert_called_once_with(
            [
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
            ],
        )
        mock_get_sherpa_qualified.reset_mock()
        mock_get_scout_qualified.reset_mock()

    @patch("apps.trailblazer.views.get_xbox_earn_sets")
    @patch("apps.trailblazer.views.get_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_trailblazer_scout_progress_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_discord_earn_dict,
        mock_get_xbox_earn_sets,
    ):
        # Missing field values throw errors
        response = self.client.post("/trailblazer/scout-progress", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUserTag", details)
        self.assertEqual(
            details.get("discordUserTag"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted value throws errors
        response = self.client.post(
            "/trailblazer/scout-progress",
            {"discordUserId": "abc", "discordUserTag": "foo"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUserTag", details)
        self.assertEqual(
            details.get("discordUserTag")[0],
            ErrorDetail(
                string="Only characters constituting a valid Discord Tag are allowed.",
                code="invalid",
            ),
        )

        # Create test data
        mock_get_xuid_and_exact_gamertag.return_value = (4567, "test1234")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="1234", discord_tag="TestTag#1234"
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

        # Exception in get_discord_earn_dict throws error
        mock_get_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_discord_earn_dict.side_effect = None
        mock_get_discord_earn_dict.reset_mock()

        # Exception in get_xbox_earn_sets throws error
        mock_get_xbox_earn_sets.side_effect = Exception()
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_xbox_earn_sets.assert_called_once_with([link.xbox_live_account_id])
        mock_get_xbox_earn_sets.side_effect = None
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_sets.reset_mock()

        # Success - point totals come through for all values
        mock_get_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "church_of_the_crab": 3,
                "sharing_is_caring": 1,
                "bookworm": 1,
            }
        }
        mock_get_xbox_earn_sets.return_value = (
            {link.xbox_live_account_id},
            {link.xbox_live_account_id},
            {link.xbox_live_account_id},
            {link.xbox_live_account_id},
        )
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_xbox_earn_sets.assert_called_once_with([link.xbox_live_account_id])
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_sets.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "church_of_the_crab": 3,
                "sharing_is_caring": 1,
                "bookworm": 1,
            }
        }
        mock_get_xbox_earn_sets.return_value = (
            {xbox_live_account.xuid},
            {xbox_live_account.xuid},
            {xbox_live_account.xuid},
            {xbox_live_account.xuid},
        )
        response = self.client.post(
            "/trailblazer/scout-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_discord_earn_dict.assert_called_once_with([discord_account.discord_id])
        mock_get_xbox_earn_sets.assert_not_called()
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_sets.reset_mock()
