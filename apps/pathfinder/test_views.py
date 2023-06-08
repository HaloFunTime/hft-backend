import datetime
from collections import OrderedDict
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import PathfinderHikeSubmission, PathfinderWAYWOPost
from apps.xbox_live.models import XboxLiveAccount


class PathfinderTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_hike_queue_view_get(self):
        # Success - nothing in queue
        response = self.client.get("/pathfinder/hike-queue", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("scheduled"), [])
        self.assertEqual(response.data.get("unscheduled"), [])

        # Create test data
        range_bound = 7
        discord_accounts = []
        for i in range(range_bound):
            discord_accounts.append(
                DiscordAccount.objects.create(
                    creator=self.user,
                    discord_id=str(i),
                    discord_username=f"TestUsername{i}",
                )
            )
        hike_submissions = []
        for i in range(range_bound):
            hike_submissions.append(
                PathfinderHikeSubmission.objects.create(
                    creator=self.user,
                    waywo_post_title=f"post{i}",
                    waywo_post_id=f"{i}",
                    map_submitter_discord=discord_accounts[i],
                    scheduled_playtest_date=(
                        datetime.date(2023, 7, i) if i % 2 == 1 else None
                    ),
                    max_player_count=f"max_player_count_{i}",
                    map=f"map{i}",
                    mode_1=f"mode_1_{i}",
                    mode_2=f"mode_2_{i}",
                )
            )

        # Success - queue returned
        response = self.client.get("/pathfinder/hike-queue", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data.get("scheduled"),
            [
                OrderedDict(
                    {
                        "waywoPostId": "1",
                        "mapSubmitterDiscordId": "1",
                        "scheduledPlaytestDate": "2023-07-01",
                        "maxPlayerCount": "max_player_count_1",
                        "map": "map1",
                        "mode1": "mode_1_1",
                        "mode2": "mode_2_1",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "3",
                        "mapSubmitterDiscordId": "3",
                        "scheduledPlaytestDate": "2023-07-03",
                        "maxPlayerCount": "max_player_count_3",
                        "map": "map3",
                        "mode1": "mode_1_3",
                        "mode2": "mode_2_3",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "5",
                        "mapSubmitterDiscordId": "5",
                        "scheduledPlaytestDate": "2023-07-05",
                        "maxPlayerCount": "max_player_count_5",
                        "map": "map5",
                        "mode1": "mode_1_5",
                        "mode2": "mode_2_5",
                    }
                ),
            ],
        )
        self.assertEqual(
            response.data.get("unscheduled"),
            [
                OrderedDict(
                    {
                        "waywoPostId": "0",
                        "mapSubmitterDiscordId": "0",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_0",
                        "map": "map0",
                        "mode1": "mode_1_0",
                        "mode2": "mode_2_0",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "2",
                        "mapSubmitterDiscordId": "2",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_2",
                        "map": "map2",
                        "mode1": "mode_1_2",
                        "mode2": "mode_2_2",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "4",
                        "mapSubmitterDiscordId": "4",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_4",
                        "map": "map4",
                        "mode1": "mode_1_4",
                        "mode2": "mode_2_4",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "6",
                        "mapSubmitterDiscordId": "6",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_6",
                        "map": "map6",
                        "mode1": "mode_1_6",
                        "mode2": "mode_2_6",
                    }
                ),
            ],
        )

    def test_hike_submission_view_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/hike-submission", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "waywoPostTitle",
            "waywoPostId",
            "mapSubmitterDiscordId",
            "mapSubmitterDiscordUsername",
            "maxPlayerCount",
            "map",
            "mode1",
            "mode2",
        ]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ"
                "ABCDEFGHIJKLMNOPQRSTUVWXYZABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "waywoPostId": "abc",
                "mapSubmitterDiscordId": "abc",
                "mapSubmitterDiscordUsername": "a",
                "maxPlayerCount": "abc",
                "map": "abc",
                "mode1": "abc",
                "mode2": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("waywoPostTitle", details)
        self.assertEqual(
            details.get("waywoPostTitle")[0],
            ErrorDetail(
                string="Ensure this field has no more than 100 characters.",
                code="max_length",
            ),
        )
        for id_field in ["waywoPostId", "mapSubmitterDiscordId"]:
            self.assertIn(id_field, details)
            self.assertEqual(
                details.get(id_field)[0],
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                ),
            )
        self.assertIn("mapSubmitterDiscordUsername", details)
        self.assertEqual(
            details.get("mapSubmitterDiscordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # Successful submission creates PathfinderHikeSubmission, DiscordAccount
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordUsername": "Test1234",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode1": "TestMode1",
                "mode2": "TestMode2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        pf_hike_submission = PathfinderHikeSubmission.objects.first()
        self.assertEqual(pf_hike_submission.waywo_post_title, "Test Title")
        self.assertEqual(pf_hike_submission.waywo_post_id, "7890")
        self.assertEqual(pf_hike_submission.map_submitter_discord.discord_id, "1234")
        self.assertEqual(
            pf_hike_submission.map_submitter_discord.discord_username, "Test1234"
        )
        self.assertEqual(pf_hike_submission.max_player_count, "8 players")
        self.assertEqual(pf_hike_submission.map, "TestMap")
        self.assertEqual(pf_hike_submission.mode_1, "TestMode1")
        self.assertEqual(pf_hike_submission.mode_2, "TestMode2")

        # Multiple submissions of same WAYWO post are forbidden if previous submission hasn't been playtested yet
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "3456",
                "mapSubmitterDiscordUsername": "Test3456",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode1": "TestModeA",
                "mode2": "TestModeB",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="A Pathfinder Hike submission already exists for this post.",
                code="permission_denied",
            ),
        )

        # Multiple submissions from the same submitter are forbidden if previous submission hasn't been playtested yet
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "0987",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordUsername": "Test1234",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode1": "TestModeA",
                "mode2": "TestModeB",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="A Pathfinder Hike submission has already been created by this Discord user.",
                code="permission_denied",
            ),
        )

    @patch("apps.pathfinder.views.is_dynamo_qualified")
    @patch("apps.pathfinder.views.is_illuminated_qualified")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_pathfinder_seasonal_role_check_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_is_illuminated_qualified,
        mock_is_dynamo_qualified,
    ):
        # Missing field values throw errors
        response = self.client.post(
            "/pathfinder/seasonal-role-check", {}, format="json"
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

        # Improperly formatted value throws errors
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {"discordUserId": "abc", "discordUsername": "f"},
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
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # Create some test data
        mock_get_xuid_and_exact_gamertag.return_value = (0, "test0")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="0", discord_username="TestUsername01234"
        )
        xbox_live_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="testGT0"
        )
        link = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account=discord_account,
            xbox_live_account=xbox_live_account,
            verified=True,
        )

        # Exception in is_illuminated_qualified throws error
        mock_is_illuminated_qualified.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {
                "discordUserId": link.discord_account.discord_id,
                "discordUsername": link.discord_account.discord_username,
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
        mock_is_illuminated_qualified.assert_called_once_with(link.xbox_live_account_id)
        mock_is_illuminated_qualified.side_effect = None
        mock_is_illuminated_qualified.reset_mock()

        # Exception in is_dynamo_qualified throws error
        mock_is_dynamo_qualified.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/seasonal-role-check",
            {
                "discordUserId": link.discord_account.discord_id,
                "discordUsername": link.discord_account.discord_username,
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
        mock_is_dynamo_qualified.assert_called_once_with(
            link.discord_account_id, link.xbox_live_account_id
        )
        mock_is_dynamo_qualified.side_effect = None
        mock_is_illuminated_qualified.reset_mock()
        mock_is_dynamo_qualified.reset_mock()

        # All permutations of qualification work
        for tuple in [(True, True), (True, False), (False, True), (False, False)]:
            mock_is_illuminated_qualified.return_value = tuple[0]
            mock_is_dynamo_qualified.return_value = tuple[1]
            response = self.client.post(
                "/pathfinder/seasonal-role-check",
                {
                    "discordUserId": link.discord_account.discord_id,
                    "discordUsername": link.discord_account.discord_username,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data.get("discordUserId"), link.discord_account_id
            )
            self.assertEqual(response.data.get("illuminated"), tuple[0])
            self.assertEqual(response.data.get("dynamo"), tuple[1])
            mock_is_illuminated_qualified.assert_called_once_with(
                link.xbox_live_account_id
            )
            mock_is_dynamo_qualified.assert_called_once_with(
                link.discord_account_id, link.xbox_live_account_id
            )
            mock_is_illuminated_qualified.reset_mock()
            mock_is_dynamo_qualified.reset_mock()

        # Deleting the DiscordXboxLiveLink record changes calls to utility methods; Illuminated is always False
        link.delete()
        for tuple in [(True, True), (True, False), (False, True), (False, False)]:
            mock_is_illuminated_qualified.return_value = tuple[0]
            mock_is_dynamo_qualified.return_value = tuple[1]
            response = self.client.post(
                "/pathfinder/seasonal-role-check",
                {
                    "discordUserId": link.discord_account.discord_id,
                    "discordUsername": link.discord_account.discord_username,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.data.get("discordUserId"), link.discord_account_id
            )
            self.assertEqual(
                response.data.get("illuminated"), False
            )  # Should be permanently false
            self.assertEqual(response.data.get("dynamo"), tuple[1])
            mock_is_illuminated_qualified.assert_not_called()
            mock_is_dynamo_qualified.assert_called_once_with(
                link.discord_account_id, None
            )
            mock_is_illuminated_qualified.reset_mock()
            mock_is_dynamo_qualified.reset_mock()

    def test_pathfinder_waywo_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/waywo-post", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "posterDiscordId",
            "posterDiscordUsername",
            "postId",
            "postTitle",
        ]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/pathfinder/waywo-post",
            {
                "posterDiscordId": "abc",
                "posterDiscordUsername": "a",
                "postId": "abc",
                "postTitle": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for id_field in ["posterDiscordId", "postId"]:
            self.assertIn(id_field, details)
            self.assertEqual(
                details.get(id_field)[0],
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                ),
            )
        self.assertIn("posterDiscordUsername", details)
        self.assertEqual(
            details.get("posterDiscordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # Success (excluding channel name)
        response = self.client.post(
            "/pathfinder/waywo-post",
            {
                "posterDiscordId": "123",
                "posterDiscordUsername": "Test0123",
                "postId": "456",
                "postTitle": "My Test Map",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        waywo_post = PathfinderWAYWOPost.objects.first()
        self.assertEqual(waywo_post.poster_discord.discord_id, "123")
        self.assertEqual(waywo_post.poster_discord.discord_username, "Test0123")
        self.assertEqual(waywo_post.post_id, "456")
        self.assertEqual(waywo_post.post_title, "My Test Map")
        waywo_post.delete()

    def test_pathfinder_dynamo_progress_view_request_errors(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/dynamo-progress", {}, format="json")
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

        # Improperly formatted value throws errors
        response = self.client.post(
            "/pathfinder/dynamo-progress",
            {"discordUserId": "abc", "discordUsername": "f"},
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
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

    @patch("apps.pathfinder.views.get_s3_xbox_earn_dict")
    @patch("apps.pathfinder.views.get_s3_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.pathfinder.views.get_current_season_id")
    def test_pathfinder_dynamo_progress_view_s3(
        self,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s3_discord_earn_dict,
        mock_get_s3_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "3"

        # Create test data
        mock_get_xuid_and_exact_gamertag.return_value = (4567, "test1234")
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="1234", discord_username="TestUsername1234"
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

        # Exception in get_s3_discord_earn_dict throws error
        mock_get_s3_discord_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/dynamo-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Pathfinder Dynamo progress check.",
                code="error",
            ),
        )
        mock_get_s3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s3_discord_earn_dict.side_effect = None
        mock_get_s3_discord_earn_dict.reset_mock()

        # Exception in get_s3_xbox_earn_dict throws error
        mock_get_s3_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/dynamo-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Error attempting the Pathfinder Dynamo progress check.",
                code="error",
            ),
        )
        mock_get_s3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s3_xbox_earn_dict.side_effect = None
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_s3_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "gone_hiking": 150,
                "map_maker": 50,
                "show_and_tell": 50,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "bookmarked": 100,
                "playtime": 100,
                "tagtacular": 50,
                "forged_in_fire": 37,
            }
        }
        response = self.client.post(
            "/pathfinder/dynamo-progress",
            {
                "discordUserId": link.discord_account_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("totalPoints"), 537)
        self.assertEqual(response.data.get("pointsGoneHiking"), 150)
        self.assertEqual(response.data.get("pointsMapMaker"), 50)
        self.assertEqual(response.data.get("pointsShowAndTell"), 50)
        self.assertEqual(response.data.get("pointsBookmarked"), 100)
        self.assertEqual(response.data.get("pointsPlaytime"), 100)
        self.assertEqual(response.data.get("pointsTagtacular"), 50)
        self.assertEqual(response.data.get("pointsForgedInFire"), 37)
        mock_get_s3_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s3_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_s3_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "gone_hiking": 150,
                "map_maker": 50,
                "show_and_tell": 50,
            }
        }
        mock_get_s3_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "bookmarked": 100,
                "playtime": 100,
                "tagtacular": 50,
                "forged_in_fire": 37,
            }
        }
        response = self.client.post(
            "/pathfinder/dynamo-progress",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("totalPoints"), 250)
        self.assertEqual(response.data.get("pointsGoneHiking"), 150)
        self.assertEqual(response.data.get("pointsMapMaker"), 50)
        self.assertEqual(response.data.get("pointsShowAndTell"), 50)
        self.assertEqual(response.data.get("pointsBookmarked"), 0)
        self.assertEqual(response.data.get("pointsPlaytime"), 0)
        self.assertEqual(response.data.get("pointsTagtacular"), 0)
        self.assertEqual(response.data.get("pointsForgedInFire"), 0)
        mock_get_s3_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_s3_xbox_earn_dict.assert_not_called()
        mock_get_s3_discord_earn_dict.reset_mock()
        mock_get_s3_xbox_earn_dict.reset_mock()

    @patch("apps.pathfinder.views.get_s4_xbox_earn_dict")
    @patch("apps.pathfinder.views.get_s4_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.pathfinder.views.get_current_season_id")
    def test_pathfinder_dynamo_progress_view_s4(
        self,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s4_discord_earn_dict,
        mock_get_s4_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "4"

        # TODO: Complete this test.
