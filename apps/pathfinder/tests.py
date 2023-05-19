import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import (
    PathfinderHikeAttendance,
    PathfinderHikeSubmission,
    PathfinderWAYWOPost,
)
from apps.pathfinder.utils import (
    get_s3_discord_earn_dict,
    get_s3_xbox_earn_dict,
    is_dynamo_qualified,
    is_illuminated_qualified,
)
from apps.xbox_live.models import XboxLiveAccount


class PathfinderUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_s3_discord_earn_dict(self):
        # Create some test data
        discord_accounts = []
        for i in range(2):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user, discord_id=str(i), discord_tag=f"TestTag{i}#1234"
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
                    category="Arena",
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
                    category="Arena",
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
                    category="Arena",
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

    def test_get_s3_xbox_earn_dict(self):
        earn_dict = get_s3_xbox_earn_dict([])
        self.assertEqual(earn_dict, {})
        # TODO: Write a more meaningful unit test for this

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

    @patch("apps.pathfinder.utils.get_s3_xbox_earn_dict")
    @patch("apps.pathfinder.utils.get_s3_discord_earn_dict")
    def test_is_dynamo_qualified(
        self,
        mock_get_s3_discord_earn_dict,
        mock_get_s3_xbox_earn_dict,
    ):
        # Null value provided to method returns False
        mock_get_s3_xbox_earn_dict.return_value = {}
        result = is_dynamo_qualified(None, None)
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
        result = is_dynamo_qualified("0", 0)
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
        result = is_dynamo_qualified("0", 0)
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
        result = is_dynamo_qualified("0", 0)
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
        result = is_dynamo_qualified("0", 0)
        self.assertEqual(result, True)
        mock_get_s3_discord_earn_dict.assert_called_once_with(["0"])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([0])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()
