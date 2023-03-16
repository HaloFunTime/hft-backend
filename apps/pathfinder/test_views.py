import datetime
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

    def test_hike_submission_view_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/hike-submission", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "waywoPostTitle",
            "waywoPostId",
            "mapSubmitterDiscordId",
            "mapSubmitterDiscordTag",
            "scheduledPlaytestDate",
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
                "mapSubmitterDiscordTag": "abc",
                "scheduledPlaytestDate": "abc",
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
        self.assertIn("mapSubmitterDiscordTag", details)
        self.assertEqual(
            details.get("mapSubmitterDiscordTag")[0],
            ErrorDetail(
                string="Only characters constituting a valid Discord Tag are allowed.",
                code="invalid",
            ),
        )

        # Successful submission creates PathfinderHikeSubmission, DiscordAccount
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordTag": "Test#1234",
                "scheduledPlaytestDate": "2023-03-15",
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
            pf_hike_submission.map_submitter_discord.discord_tag, "Test#1234"
        )
        self.assertEqual(
            pf_hike_submission.scheduled_playtest_date,
            datetime.date(year=2023, month=3, day=15),
        )
        self.assertEqual(pf_hike_submission.map, "TestMap")
        self.assertEqual(pf_hike_submission.mode_1, "TestMode1")
        self.assertEqual(pf_hike_submission.mode_2, "TestMode2")

        # Multiple submissions of same WAYWO post are forbidden if scheduled for the same day
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "3456",
                "mapSubmitterDiscordTag": "Test#3456",
                "scheduledPlaytestDate": "2023-03-15",
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

        # Multiple submissions from the same submitter are forbidden if scheduled for the same day
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "0987",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordTag": "Test#1234",
                "scheduledPlaytestDate": "2023-03-15",
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

    @patch("apps.pathfinder.views.get_dynamo_qualified")
    @patch("apps.pathfinder.views.get_illuminated_qualified")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_pathfinder_seasonal_role_check_view(
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

    def test_pathfinder_waywo_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/waywo-post", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "posterDiscordId",
            "posterDiscordTag",
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
                "posterDiscordTag": "abc",
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
        self.assertIn("posterDiscordTag", details)
        self.assertEqual(
            details.get("posterDiscordTag")[0],
            ErrorDetail(
                string="Only characters constituting a valid Discord Tag are allowed.",
                code="invalid",
            ),
        )

        # Success (excluding channel name)
        response = self.client.post(
            "/pathfinder/waywo-post",
            {
                "posterDiscordId": "123",
                "posterDiscordTag": "Test#0123",
                "postId": "456",
                "postTitle": "My Test Map",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_tag, "Test#0123")
        waywo_post = PathfinderWAYWOPost.objects.first()
        self.assertEqual(waywo_post.poster_discord.discord_id, "123")
        self.assertEqual(waywo_post.poster_discord.discord_tag, "Test#0123")
        self.assertEqual(waywo_post.post_id, "456")
        self.assertEqual(waywo_post.post_title, "My Test Map")
        waywo_post.delete()

    @patch("apps.pathfinder.views.get_xbox_earn_dict")
    @patch("apps.pathfinder.views.get_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_pathfinder_dynamo_progress_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_discord_earn_dict,
        mock_get_xbox_earn_dict,
    ):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/dynamo-progress", {}, format="json")
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
            "/pathfinder/dynamo-progress",
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
            "/pathfinder/dynamo-progress",
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
                string="Error attempting the Pathfinder Dynamo progress check.",
                code="error",
            ),
        )
        mock_get_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_discord_earn_dict.side_effect = None
        mock_get_discord_earn_dict.reset_mock()

        # Exception in get_xbox_earn_dict throws error
        mock_get_xbox_earn_dict.side_effect = Exception()
        response = self.client.post(
            "/pathfinder/dynamo-progress",
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
                string="Error attempting the Pathfinder Dynamo progress check.",
                code="error",
            ),
        )
        mock_get_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_xbox_earn_dict.side_effect = None
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "gone_hiking": 150,
                "map_maker": 50,
                "show_and_tell": 50,
            }
        }
        mock_get_xbox_earn_dict.return_value = {
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
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_discord_earn_dict.return_value = {
            discord_account.discord_id: {
                "gone_hiking": 150,
                "map_maker": 50,
                "show_and_tell": 50,
            }
        }
        mock_get_xbox_earn_dict.return_value = {
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
                "discordUserTag": discord_account.discord_tag,
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
        mock_get_discord_earn_dict.assert_called_once_with([discord_account.discord_id])
        mock_get_xbox_earn_dict.assert_not_called()
        mock_get_discord_earn_dict.reset_mock()
        mock_get_xbox_earn_dict.reset_mock()
