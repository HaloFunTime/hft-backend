from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.trailblazers.utils import get_sherpa_qualified
from apps.xbox_live.models import XboxLiveAccount


class TrailblazerUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.trailblazers.utils.get_csrs")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_get_sherpa_qualified(
        self, mock_get_xuid_and_exact_gamertag, mock_get_csrs
    ):
        # Empty list provided to method returns nothing
        mock_get_csrs.return_value = {"csrs": {}}
        result = get_sherpa_qualified([])
        self.assertEqual(result, [])
        mock_get_csrs.assert_called_once_with(
            [], "edfef3ac-9cbe-4fa2-b949-8f29deafd483"
        )
        mock_get_csrs.reset_mock()

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

        # Success - some current reset max CSRs over 1650 in payload
        mock_get_csrs.return_value = {
            "csrs": {
                0: {
                    "current_reset_max_csr": 1433,
                },
                1: {
                    "current_reset_max_csr": 1840,
                },
                2: {
                    "current_reset_max_csr": 1573,
                },
                3: {
                    "current_reset_max_csr": 1222,
                },
                4: {
                    "current_reset_max_csr": 780,
                },
                5: {
                    "current_reset_max_csr": -1,
                },
                6: {
                    "current_reset_max_csr": 1900,
                },
                7: {
                    "current_reset_max_csr": 1650,
                },
                8: {
                    "current_reset_max_csr": 1649,
                },
                9: {
                    "current_reset_max_csr": 1651,
                },
            }
        }
        result = get_sherpa_qualified(links)
        self.assertEqual(result, ["1", "6", "7", "9"])
        mock_get_csrs.assert_called_once_with(
            [link.xbox_live_account_id for link in links],
            "edfef3ac-9cbe-4fa2-b949-8f29deafd483",
        )
        mock_get_csrs.reset_mock()

    def test_get_scout_qualified(self):
        # TODO: Test Scout logic after implementation
        pass
