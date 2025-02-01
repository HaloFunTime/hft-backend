from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.halo_infinite.constants import (
    ERA_1_START_TIME,
    ERA_2_START_TIME,
    ERA_3_START_TIME,
)
from apps.pathfinder.models import (
    PathfinderBeanCount,
    PathfinderHikeSubmission,
    PathfinderWAYWOComment,
    PathfinderWAYWOPost,
)
from apps.pathfinder.utils import (
    change_beans,
    check_beans,
    get_e1_discord_earn_dict,
    get_e2_discord_earn_dict,
    get_e3_discord_earn_dict,
)


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

    def test_get_e1_discord_earn_dict(self):
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
        earn_dict = get_e1_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # TODO: Complete this test.

    def test_get_e2_discord_earn_dict(self):
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
        earn_dict = get_e2_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        hike_submissions = []
        waywo_posts = []
        waywo_comments = []
        hike_submissions.append(
            PathfinderHikeSubmission.objects.create(
                creator=self.user,
                map_submitter_discord=discord_accounts[0],
            )
        )
        PathfinderHikeSubmission.objects.all().update(created_at=ERA_2_START_TIME)
        for i in range(3):
            waywo_posts.append(
                PathfinderWAYWOPost.objects.create(
                    creator=self.user,
                    poster_discord=discord_accounts[0],
                )
            )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_2_START_TIME)
        for i in range(100):
            waywo_comments.append(
                PathfinderWAYWOComment.objects.create(
                    creator=self.user,
                    commenter_discord=discord_accounts[0],
                    comment_length=100,
                )
            )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_2_START_TIME)
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bean_spender"], 200)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 150
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 100
        )

        # Max points - overages
        hike_submissions.append(
            PathfinderHikeSubmission.objects.create(
                creator=self.user,
                map_submitter_discord=discord_accounts[0],
            )
        )
        PathfinderHikeSubmission.objects.all().update(created_at=ERA_2_START_TIME)
        waywo_posts.append(
            PathfinderWAYWOPost.objects.create(
                creator=self.user,
                poster_discord=discord_accounts[0],
            )
        )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_2_START_TIME)
        waywo_comments.append(
            PathfinderWAYWOComment.objects.create(
                creator=self.user,
                commenter_discord=discord_accounts[0],
                comment_length=100,
            )
        )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_2_START_TIME)
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bean_spender"], 200)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 150
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 100
        )

        # Deletion of all records eliminates points
        PathfinderHikeSubmission.objects.all().delete()
        PathfinderWAYWOPost.objects.all().delete()
        PathfinderWAYWOComment.objects.all().delete()
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bean_spender"], 0)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 0)

        # Addition of records outside the date range still results in no points
        hike_submissions.append(
            PathfinderHikeSubmission.objects.create(
                creator=self.user,
                map_submitter_discord=discord_accounts[0],
            )
        )
        PathfinderHikeSubmission.objects.all().update(created_at=ERA_1_START_TIME)
        waywo_posts.append(
            PathfinderWAYWOPost.objects.create(
                creator=self.user,
                poster_discord=discord_accounts[0],
            )
        )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_1_START_TIME)
        waywo_comments.append(
            PathfinderWAYWOComment.objects.create(
                creator=self.user,
                commenter_discord=discord_accounts[0],
                comment_length=100,
            )
        )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_1_START_TIME)
        earn_dict = get_e2_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["bean_spender"], 0)
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 0)

    def test_get_e3_discord_earn_dict(self):
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
        earn_dict = get_e3_discord_earn_dict([])
        self.assertEqual(earn_dict, {})

        # Max Points - exactly
        waywo_posts = []
        waywo_comments = []
        for i in range(2):
            waywo_posts.append(
                PathfinderWAYWOPost.objects.create(
                    creator=self.user,
                    poster_discord=discord_accounts[0],
                )
            )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_3_START_TIME)
        for i in range(300):
            waywo_comments.append(
                PathfinderWAYWOComment.objects.create(
                    creator=self.user,
                    commenter_discord=discord_accounts[0],
                    comment_length=100,
                )
            )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_3_START_TIME)
        earn_dict = get_e3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 200
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 300
        )

        # Max points - overages
        waywo_posts.append(
            PathfinderWAYWOPost.objects.create(
                creator=self.user,
                poster_discord=discord_accounts[0],
            )
        )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_3_START_TIME)
        waywo_comments.append(
            PathfinderWAYWOComment.objects.create(
                creator=self.user,
                commenter_discord=discord_accounts[0],
                comment_length=100,
            )
        )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_3_START_TIME)
        earn_dict = get_e3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 200
        )
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 300
        )

        # Deletion of all records eliminates points
        PathfinderWAYWOPost.objects.all().delete()
        PathfinderWAYWOComment.objects.all().delete()
        earn_dict = get_e3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 0)

        # Addition of records outside the date range still results in no points
        waywo_posts.append(
            PathfinderWAYWOPost.objects.create(
                creator=self.user,
                poster_discord=discord_accounts[0],
            )
        )
        PathfinderWAYWOPost.objects.all().update(created_at=ERA_1_START_TIME)
        waywo_comments.append(
            PathfinderWAYWOComment.objects.create(
                creator=self.user,
                commenter_discord=discord_accounts[0],
                comment_length=100,
            )
        )
        PathfinderWAYWOComment.objects.all().update(created_at=ERA_1_START_TIME)
        earn_dict = get_e3_discord_earn_dict([discord_accounts[0].discord_id])
        self.assertEqual(
            earn_dict[discord_accounts[0].discord_id]["what_are_you_working_on"], 0
        )
        self.assertEqual(earn_dict[discord_accounts[0].discord_id]["feedback_fiend"], 0)
