import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import (
    PathfinderBeanCount,
    PathfinderHikeAttendance,
    PathfinderHikeSubmission,
    PathfinderWAYWOPost,
)
from apps.pathfinder.utils import (
    change_beans,
    check_beans,
    get_s3_discord_earn_dict,
    get_s4_discord_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
    is_s3_dynamo_qualified,
    is_s4_dynamo_qualified,
)
from apps.xbox_live.models import XboxLiveAccount


class PathfinderUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.pathfinder.utils.check_beans")
    def test_change_beans(self, mock_check_beans):
        discord_account = DiscordAccount.objects.create(
            discord_id="123", discord_username="Test123", creator=self.user
        )
        pbc = PathfinderBeanCount.objects.create(
            bean_owner_discord=discord_account, bean_count=0, creator=self.user
        )

        # Successful change (adds 10 beans)
        mock_check_beans.return_value = 0
        success = change_beans(discord_account, 10)
        self.assertTrue(success)
        mock_check_beans.assert_called_once_with(discord_account)
        pbc.refresh_from_db()
        self.assertEqual(pbc.bean_count, 10)
        mock_check_beans.reset_mock()

        # Successful change (removes 5 beans)
        mock_check_beans.return_value = 10
        success = change_beans(discord_account, -5)
        self.assertTrue(success)
        mock_check_beans.assert_called_once_with(discord_account)
        pbc.refresh_from_db()
        self.assertEqual(pbc.bean_count, 5)
        mock_check_beans.reset_mock()

        # Unsuccessful change (removes no beans)
        mock_check_beans.return_value = 5
        success = change_beans(discord_account, -6)
        self.assertFalse(success)
        mock_check_beans.assert_called_once_with(discord_account)
        pbc.refresh_from_db()
        self.assertEqual(pbc.bean_count, 5)
        mock_check_beans.reset_mock()

    def test_check_beans(self):
        discord_account = DiscordAccount.objects.create(
            discord_id="123", discord_username="Test123", creator=self.user
        )

        # Nonexistent PathfinderBeanCount record leads to creation of one
        bean_count = check_beans(discord_account)
        self.assertEqual(bean_count, 0)
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pbc = PathfinderBeanCount.objects.first()
        self.assertEqual(pbc.bean_owner_discord, discord_account)
        self.assertEqual(pbc.bean_count, 0)

        # Existing PathfinderBeanCount count is returned
        pbc.bean_count = 50
        pbc.save()
        bean_count = check_beans(discord_account)
        self.assertEqual(pbc.bean_count, 50)

        # Call with None raises
        self.assertRaises(AssertionError, check_beans, None)

    def test_get_s3_discord_earn_dict(self):
        # Create some test data
        discord_accounts = []
        for i in range(2):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user,
                    discord_id=str(i),
                    discord_username=f"TestUsername{i}",
                )
            )

        # No IDs = No earn dicts
        earn_dict = get_s3_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        ghs = []
        for i in range(5):
            ghs.append(
                PathfinderHikeAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 4, 6),
                )
            )
        mms = []
        for i in range(3):
            mms.append(
                PathfinderHikeSubmission.objects.create(
                    creator=self.user,
                    waywo_post_title=f"post{i}",
                    waywo_post_id=f"{i}",
                    map_submitter_discord=discord_accounts[0],
                    scheduled_playtest_date=datetime.date(2023, 4, 6),
                    max_player_count="4 players",
                    map=f"map{i}",
                    mode_1=f"mode_1_{i}",
                    mode_2=f"mode_2_{i}",
                )
            )
        sats = []
        for i in range(2):
            waywo_post = PathfinderWAYWOPost.objects.create(
                creator=self.user,
                post_title=f"post{i}",
                post_id=f"{i}",
                poster_discord=discord_accounts[0],
            )
            waywo_post.created_at = datetime.datetime(2023, 4, 6)
            waywo_post.save()
            sats.append(waywo_post)
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["gone_hiking"], 250)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["map_maker"], 150)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["show_and_tell"], 100
        )

        # Max points - overages
        for i in range(2):
            ghs.append(
                PathfinderHikeAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 4, 6),
                )
            )
            mms.append(
                PathfinderHikeSubmission.objects.create(
                    creator=self.user,
                    waywo_post_title=f"post{i}",
                    waywo_post_id=f"{i}",
                    map_submitter_discord=discord_accounts[0],
                    scheduled_playtest_date=datetime.date(2023, 4, 6),
                    max_player_count="4 players",
                    map=f"map{i}",
                    mode_1=f"mode_1_{i}",
                    mode_2=f"mode_2_{i}",
                )
            )
            waywo_post = PathfinderWAYWOPost.objects.create(
                creator=self.user,
                post_title=f"post{i}",
                post_id=f"{i}",
                poster_discord=discord_accounts[0],
            )
            waywo_post.created_at = datetime.datetime(2023, 4, 6)
            waywo_post.save()
            sats.append(waywo_post)
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["gone_hiking"], 250)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["map_maker"], 150)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["show_and_tell"], 100
        )

        # Deletion of all records eliminates points
        for gh in ghs:
            gh.delete()
        for mm in mms:
            mm.delete()
        for sat in sats:
            sat.delete()
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["gone_hiking"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["map_maker"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["show_and_tell"], 0)

        # Addition of records outside the date range still results in no points
        ghs = []
        for i in range(5):
            ghs.append(
                PathfinderHikeAttendance.objects.create(
                    creator=self.user,
                    attendee_discord=discord_accounts[0],
                    attendance_date=datetime.date(2023, 7, 6),
                )
            )
        mms = []
        for i in range(3):
            mms.append(
                PathfinderHikeSubmission.objects.create(
                    creator=self.user,
                    waywo_post_title=f"post{i}",
                    waywo_post_id=f"{i}",
                    map_submitter_discord=discord_accounts[0],
                    scheduled_playtest_date=datetime.date(2023, 7, 6),
                    max_player_count="4 players",
                    map=f"map{i}",
                    mode_1=f"mode_1_{i}",
                    mode_2=f"mode_2_{i}",
                )
            )
        sats = []
        for i in range(2):
            waywo_post = PathfinderWAYWOPost.objects.create(
                creator=self.user,
                post_title=f"post{i}",
                post_id=f"{i}",
                poster_discord=discord_accounts[0],
            )
            waywo_post.created_at = datetime.datetime(2023, 7, 6)
            waywo_post.save()
            sats.append(waywo_post)
        earn_dict = get_s3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["gone_hiking"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["map_maker"], 0)
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["show_and_tell"], 0)

    @patch("apps.pathfinder.utils.get_s3_xbox_earn_dict")
    @patch("apps.pathfinder.utils.get_s3_discord_earn_dict")
    def test_is_s3_dynamo_qualified(
        self,
        mock_get_s3_discord_earn_dict,
        mock_get_s3_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_s3_xbox_earn_dict.return_value = {}
        result = is_s3_dynamo_qualified(None, None)
        self.assertEqual(result, False)

        # No points means not qualified
        mock_get_s3_discord_earn_dict.return_value = {
            "0": {
                "gone_hiking": 0,
                "map_maker": 0,
                "show_and_tell": 0,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            0: {
                "bookmarked": 0,
                "playtime": 0,
                "tagtacular": 0,
                "forged_in_fire": 0,
            }
        }
        result = is_s3_dynamo_qualified("0", 0)
        self.assertEqual(result, False)
        mock_get_s3_discord_earn_dict.assert_called_once_with(["0"])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([0])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Some points, not qualified
        mock_get_s3_discord_earn_dict.return_value = {
            "0": {
                "gone_hiking": 100,
                "map_maker": 50,
                "show_and_tell": 50,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            0: {
                "bookmarked": 0,
                "playtime": 0,
                "tagtacular": 25,
                "forged_in_fire": 78,
            }
        }
        result = is_s3_dynamo_qualified("0", 0)
        self.assertEqual(result, False)
        mock_get_s3_discord_earn_dict.assert_called_once_with(["0"])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([0])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Max discord points, qualified
        mock_get_s3_discord_earn_dict.return_value = {
            "0": {
                "gone_hiking": 250,
                "map_maker": 150,
                "show_and_tell": 100,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            0: {
                "bookmarked": 0,
                "playtime": 0,
                "tagtacular": 0,
                "forged_in_fire": 0,
            }
        }
        result = is_s3_dynamo_qualified("0", 0)
        self.assertEqual(result, True)
        mock_get_s3_discord_earn_dict.assert_called_once_with(["0"])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([0])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Max xbox points, qualified
        mock_get_s3_discord_earn_dict.return_value = {
            "0": {
                "gone_hiking": 0,
                "map_maker": 0,
                "show_and_tell": 0,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            0: {
                "bookmarked": 100,
                "playtime": 100,
                "tagtacular": 100,
                "forged_in_fire": 200,
            }
        }
        result = is_s3_dynamo_qualified("0", 0)
        self.assertEqual(result, True)
        mock_get_s3_discord_earn_dict.assert_called_once_with(["0"])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([0])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

    def test_get_s4_discord_earn_dict(self):
        # Create some test data
        discord_accounts = []
        for i in range(2):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user,
                    discord_id=str(i),
                    discord_username=f"TestUsername{i}",
                )
            )

        # No IDs = No earn dicts
        earn_dict = get_s4_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # TODO: Complete this test.

    @patch("apps.pathfinder.utils.get_s4_xbox_earn_dict")
    @patch("apps.pathfinder.utils.get_s4_discord_earn_dict")
    def test_is_s4_dynamo_qualified(
        self,
        mock_get_s4_discord_earn_dict,
        mock_get_s4_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_s4_xbox_earn_dict.return_value = {}
        result = is_s4_dynamo_qualified(None, None)
        self.assertEqual(result, False)

        # TODO: Complete this test.

    @patch("apps.pathfinder.utils.is_s4_dynamo_qualified")
    @patch("apps.pathfinder.utils.is_s3_dynamo_qualified")
    @patch("apps.pathfinder.utils.get_current_season_id")
    def test_is_dynamo_qualified(
        self,
        mock_get_current_season_id,
        mock_is_s3_dynamo_qualified,
        mock_is_s4_dynamo_qualified,
    ):
        def reset_all_mocks():
            mock_get_current_season_id.reset_mock()
            mock_is_s3_dynamo_qualified.reset_mock()
            mock_is_s4_dynamo_qualified.reset_mock()

        # Season 3
        mock_get_current_season_id.return_value = "3"
        mock_is_s3_dynamo_qualified.return_value = True
        result = is_dynamo_qualified("123", 123)
        self.assertEqual(result, True)
        mock_get_current_season_id.assert_called_once_with()
        mock_is_s3_dynamo_qualified.assert_called_once_with("123", 123)
        mock_is_s4_dynamo_qualified.assert_not_called()
        reset_all_mocks()

        # Season 4
        mock_get_current_season_id.return_value = "4"
        mock_is_s4_dynamo_qualified.return_value = True
        result = is_dynamo_qualified("123", 123)
        self.assertEqual(result, True)
        mock_get_current_season_id.assert_called_once_with()
        mock_is_s3_dynamo_qualified.assert_not_called()
        mock_is_s4_dynamo_qualified.assert_called_once_with("123", 123)
        reset_all_mocks()

    @patch("apps.pathfinder.utils.get_343_recommended_contributors")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_is_illuminated_qualified(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_343_recommended_contributors,
    ):
        # Null value provided to method returns False
        mock_get_343_recommended_contributors.return_value = {
            "map": {},
            "mode": {},
            "prefab": {},
        }
        result = is_illuminated_qualified(None)
        self.assertEqual(result, False)
        mock_get_343_recommended_contributors.assert_called_once_with()
        mock_get_343_recommended_contributors.reset_mock()

        # Create some test data
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

        # Returns appropriate value based on whether XUID is found with an appropriate count in the mock payload
        for i in range(10):
            mock_get_343_recommended_contributors.return_value = {
                "map": {
                    0: 1,
                    4: 1,
                    9: 2,
                },
                "mode": {
                    1: 1,
                    2: 2,
                    3: 1,
                },
                "prefab": {
                    5: 3,
                    6: 1,
                    7: 2,
                    8: 0,
                },
            }
            result = is_illuminated_qualified(i)
            self.assertEqual(result, i in {0, 2, 4, 5, 7, 9})
            mock_get_343_recommended_contributors.assert_called_once_with()
            mock_get_343_recommended_contributors.reset_mock()
