from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.utils import (
    get_discord_earn_dict,
    get_xbox_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
)
from apps.xbox_live.models import XboxLiveAccount


class PathfinderUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_discord_earn_dict(self):
        earn_dict = get_discord_earn_dict([])
        self.assertEqual(earn_dict, {})
        # TODO: Write a more meaningful unit test for this

    def test_get_xbox_earn_dict(self):
        earn_dict = get_xbox_earn_dict([])
        self.assertEqual(earn_dict, {})
        # TODO: Write a more meaningful unit test for this

    @patch("apps.pathfinder.utils.get_343_recommended_map_contributors")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_illuminated_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_343_recommended_map_contributors,
    ):
        # Null value provided to method returns False
        mock_get_343_recommended_map_contributors.return_value = {}
        result = is_illuminated_qualified(None)
        self.assertEqual(result, False)
        mock_get_343_recommended_map_contributors.assert_called_once_with()
        mock_get_343_recommended_map_contributors.reset_mock()

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

        # Returns appropriate value based on whether XUID is found as a key in the mock payload
        for i in range(10):
            mock_get_343_recommended_map_contributors.return_value = {
                0: 1,
                4: 1,
                9: 2,
            }
            result = is_illuminated_qualified(i)
            self.assertEqual(result, i in {0, 4, 9})
            mock_get_343_recommended_map_contributors.assert_called_once_with()
            mock_get_343_recommended_map_contributors.reset_mock()

    @patch("apps.pathfinder.utils.get_xbox_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_dynamo_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_xbox_earn_dict.return_value = {}
        result = is_dynamo_qualified(None, None)
        self.assertEqual(result, False)
        # TODO: Test Dynamo logic after implementation
