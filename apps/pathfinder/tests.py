from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.utils import get_illuminated_qualified
from apps.xbox_live.models import XboxLiveAccount


class PathfinderUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.pathfinder.utils.get_343_recommended_file_contributors")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_get_illuminated_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_343_recommended_file_contributors,
    ):
        # Empty list provided to method returns nothing
        mock_get_343_recommended_file_contributors.return_value = {}
        result = get_illuminated_qualified([])
        self.assertEqual(result, [])
        mock_get_343_recommended_file_contributors.assert_called_once_with()
        mock_get_343_recommended_file_contributors.reset_mock()

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

        # Success - some matching XUIDs in payload
        mock_get_343_recommended_file_contributors.return_value = {
            0: 1,
            4: 1,
            9: 2,
        }
        result = get_illuminated_qualified(links)
        self.assertEqual(result, ["0", "4", "9"])
        mock_get_343_recommended_file_contributors.assert_called_once_with()
        mock_get_343_recommended_file_contributors.reset_mock()

    def test_get_dynamo_qualified(self):
        # TODO: Test Dynamo logic after implementation
        pass
