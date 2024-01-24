import datetime
import uuid
from collections import OrderedDict
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.pathfinder.models import (
    PathfinderBeanCount,
    PathfinderHikeGameParticipation,
    PathfinderHikeSubmission,
    PathfinderHikeVoiceParticipation,
    PathfinderTestingLFGPost,
    PathfinderWAYWOComment,
    PathfinderWAYWOPost,
)
from apps.pathfinder.utils import (
    BEAN_AWARD_HIKE_GAME_PARTICIPATION,
    BEAN_AWARD_HIKE_VOICE_PARTICIPATION,
    BEAN_AWARD_WAYWO_COMMENT,
    BEAN_COST_HIKE_SUBMISSION,
)
from apps.xbox_live.models import XboxLiveAccount


class PathfinderTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_change_beans_view_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/change-beans", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordId", details)
        self.assertEqual(
            details.get("discordId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("beanDelta", details)
        self.assertEqual(
            details.get("beanDelta"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted value throws errors
        response = self.client.post(
            "/pathfinder/change-beans",
            {"discordId": "abc", "discordUsername": "f", "beanDelta": "abc"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordId", details)
        self.assertEqual(
            details.get("discordId")[0],
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
        self.assertIn("beanDelta", details)
        self.assertEqual(
            details.get("beanDelta")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # Successful change (give beans) creates DiscordAccount and PathfinderBeanCount record
        response = self.client.post(
            "/pathfinder/change-beans",
            {"discordId": "123", "discordUsername": "Test123", "beanDelta": 5},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(DiscordAccount.objects.count(), 1)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test123")
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pf_bean_count = PathfinderBeanCount.objects.first()
        self.assertEqual(pf_bean_count.bean_owner_discord, discord_account)
        self.assertEqual(pf_bean_count.bean_count, 5)

        # Successful change (take beans)
        response = self.client.post(
            "/pathfinder/change-beans",
            {"discordId": "123", "discordUsername": "Test123", "beanDelta": -4},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(DiscordAccount.objects.count(), 1)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test123")
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pf_bean_count = PathfinderBeanCount.objects.first()
        self.assertEqual(pf_bean_count.bean_owner_discord, discord_account)
        self.assertEqual(pf_bean_count.bean_count, 1)

    def test_check_beans_view_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/check-beans", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordId", details)
        self.assertEqual(
            details.get("discordId"),
            [ErrorDetail(string="This field is required.", code="required")],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted value throws errors
        response = self.client.post(
            "/pathfinder/check-beans",
            {"discordId": "abc", "discordUsername": "f"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordId", details)
        self.assertEqual(
            details.get("discordId")[0],
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

        # Check (existing Account & PBC)
        discord_account = DiscordAccount.objects.create(
            discord_id="123", discord_username="Test123", creator=self.user
        )
        pbc = PathfinderBeanCount.objects.create(
            bean_owner_discord=discord_account, bean_count=10, creator=self.user
        )
        response = self.client.post(
            "/pathfinder/check-beans",
            {"discordId": "123", "discordUsername": "Test123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("beanCount"), 10)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)

        # Check (existing Account, nonexistent PBC)
        pbc.delete()
        response = self.client.post(
            "/pathfinder/check-beans",
            {"discordId": "123", "discordUsername": "Test123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("beanCount"), 0)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test123")
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pbc = PathfinderBeanCount.objects.first()
        self.assertEqual(pbc.bean_owner_discord, discord_account)
        self.assertEqual(pbc.bean_count, 0)

        # Check (nonexistent Account & PBC)
        pbc.delete()
        discord_account.delete()
        response = self.client.post(
            "/pathfinder/check-beans",
            {"discordId": "123", "discordUsername": "Test123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("beanCount"), 0)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test123")
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pbc = PathfinderBeanCount.objects.first()
        self.assertEqual(pbc.bean_owner_discord, discord_account)
        self.assertEqual(pbc.bean_count, 0)

    @patch("apps.pathfinder.signals.match_stats")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_hike_complete_view_post(
        self, mock_get_xuid_and_exact_gamertag, mock_match_stats
    ):
        mock_match_stats.return_value = {}
        # Missing field values throw errors
        response = self.client.post("/pathfinder/hike-complete", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in ["playtestGameId", "discordUsersInVoice", "waywoPostId"]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/pathfinder/hike-complete",
            {
                "playtestGameId": "abc",
                "discordUsersInVoice": "foo",
                "waywoPostId": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("playtestGameId", details)
        self.assertEqual(
            details.get("playtestGameId")[0],
            ErrorDetail(string="Must be a valid UUID.", code="invalid"),
        )
        self.assertIn("discordUsersInVoice", details)
        self.assertEqual(
            details.get("discordUsersInVoice")[0],
            ErrorDetail(
                string='Expected a list of items but got type "str".', code="not_a_list"
            ),
        )
        self.assertIn("waywoPostId", details)
        self.assertEqual(
            details.get("waywoPostId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )

        # 403 if no Hike Submission exists for WAYWO post
        response = self.client.post(
            "/pathfinder/hike-complete",
            {
                "playtestGameId": "2028bf2d-a2c6-440b-9fe6-71e7f69376f8",
                "discordUsersInVoice": [],
                "waywoPostId": "123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Could not find an incomplete Pathfinder Hike Submission associated with this WAYWO Post.",
                code="permission_denied",
            ),
        )

        # 403 if Hike Submission exists for WAYWO post but is already complete
        submitter_discord = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_username="Test123"
        )
        PathfinderHikeSubmission.objects.create(
            creator=self.user,
            map_submitter_discord=submitter_discord,
            playtest_game_id=uuid.uuid4(),
            waywo_post_id="123",
        )
        response = self.client.post(
            "/pathfinder/hike-complete",
            {
                "playtestGameId": uuid.uuid4(),
                "discordUsersInVoice": [],
                "waywoPostId": "123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Could not find an incomplete Pathfinder Hike Submission associated with this WAYWO Post.",
                code="permission_denied",
            ),
        )

        # Happy path - three users in voice, four from game, one overlapping
        discord_accounts = []
        for i in range(6):
            mock_get_xuid_and_exact_gamertag.return_value = (i, f"test{i}")
            discord_account = DiscordAccount.objects.create(
                creator=self.user, discord_id=str(i), discord_username=f"Test{i}"
            )
            xbox_live_account = XboxLiveAccount.objects.create(
                creator=self.user, gamertag=f"testGT{i}"
            )
            DiscordXboxLiveLink.objects.create(
                creator=self.user,
                discord_account=discord_account,
                xbox_live_account=xbox_live_account,
                verified=True,
            )
            discord_accounts.append(discord_account)
        hike_submission = PathfinderHikeSubmission.objects.create(
            creator=self.user,
            map_submitter_discord=submitter_discord,
            waywo_post_id="456",
        )
        mock_match_stats.return_value = {
            "Players": [
                {
                    "PlayerId": "xuid(0)",
                    "ParticipationInfo": {
                        "PresentAtCompletion": True,
                    },
                },
                {
                    "PlayerId": "xuid(1)",
                    "ParticipationInfo": {
                        "PresentAtCompletion": True,
                    },
                },
                {
                    "PlayerId": "xuid(3)",
                    "ParticipationInfo": {
                        "PresentAtCompletion": True,
                    },
                },
                {
                    "PlayerId": "xuid(5)",
                    "ParticipationInfo": {
                        "PresentAtCompletion": True,
                    },
                },
            ]
        }
        response = self.client.post(
            "/pathfinder/hike-complete",
            {
                "playtestGameId": uuid.uuid4(),
                "discordUsersInVoice": [
                    {"discordId": "0", "discordUsername": "Test0"},
                    {"discordId": "2", "discordUsername": "Test2"},
                    {"discordId": "4", "discordUsername": "Test4"},
                ],
                "waywoPostId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PathfinderHikeGameParticipation.objects.count(), 4)
        for game_participation in PathfinderHikeGameParticipation.objects.all():
            self.assertEqual(game_participation.hike_submission_id, hike_submission.id)
        self.assertEqual(PathfinderHikeVoiceParticipation.objects.count(), 3)
        for voice_participation in PathfinderHikeVoiceParticipation.objects.all():
            self.assertEqual(voice_participation.hike_submission_id, hike_submission.id)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(
            response.data.get("awardedUsers"),
            [
                OrderedDict(
                    [
                        ("discordId", "0"),
                        ("discordUsername", "Test0"),
                        (
                            "awardedBeans",
                            BEAN_AWARD_HIKE_GAME_PARTICIPATION
                            + BEAN_AWARD_HIKE_VOICE_PARTICIPATION,
                        ),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordId", "5"),
                        ("discordUsername", "Test5"),
                        ("awardedBeans", BEAN_AWARD_HIKE_GAME_PARTICIPATION),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordId", "3"),
                        ("discordUsername", "Test3"),
                        ("awardedBeans", BEAN_AWARD_HIKE_GAME_PARTICIPATION),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordId", "1"),
                        ("discordUsername", "Test1"),
                        ("awardedBeans", BEAN_AWARD_HIKE_GAME_PARTICIPATION),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordId", "4"),
                        ("discordUsername", "Test4"),
                        ("awardedBeans", BEAN_AWARD_HIKE_VOICE_PARTICIPATION),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordId", "2"),
                        ("discordUsername", "Test2"),
                        ("awardedBeans", BEAN_AWARD_HIKE_VOICE_PARTICIPATION),
                    ]
                ),
            ],
        )
        for discord_account in discord_accounts:
            pbc = PathfinderBeanCount.objects.filter(
                bean_owner_discord=discord_account
            ).get()
            self.assertNotEqual(pbc.bean_count, 0)

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
                    mode=f"mode{i}",
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
                        "mode": "mode1",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "3",
                        "mapSubmitterDiscordId": "3",
                        "scheduledPlaytestDate": "2023-07-03",
                        "maxPlayerCount": "max_player_count_3",
                        "map": "map3",
                        "mode": "mode3",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "5",
                        "mapSubmitterDiscordId": "5",
                        "scheduledPlaytestDate": "2023-07-05",
                        "maxPlayerCount": "max_player_count_5",
                        "map": "map5",
                        "mode": "mode5",
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
                        "mode": "mode0",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "2",
                        "mapSubmitterDiscordId": "2",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_2",
                        "map": "map2",
                        "mode": "mode2",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "4",
                        "mapSubmitterDiscordId": "4",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_4",
                        "map": "map4",
                        "mode": "mode4",
                    }
                ),
                OrderedDict(
                    {
                        "waywoPostId": "6",
                        "mapSubmitterDiscordId": "6",
                        "scheduledPlaytestDate": None,
                        "maxPlayerCount": "max_player_count_6",
                        "map": "map6",
                        "mode": "mode6",
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
            "mode",
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
                "mode": "abc",
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

        # Submission fails if DiscordAccount doesn't have enough beans
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordUsername": "Test1234",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode": "TestMode",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 0)
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="This Discord user does not have enough Pathfinder Beans for a Hike submission.",
                code="permission_denied",
            ),
        )

        # Successful submission creates PathfinderHikeSubmission, DiscordAccount and subtracts Beans
        pbc = PathfinderBeanCount.objects.first()
        pbc.bean_count = BEAN_COST_HIKE_SUBMISSION
        pbc.save()
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordUsername": "Test1234",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode": "TestMode",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("success"))
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        pf_hike_submission = PathfinderHikeSubmission.objects.first()
        self.assertEqual(pf_hike_submission.waywo_post_title, "Test Title")
        self.assertEqual(pf_hike_submission.waywo_post_id, "7890")
        self.assertEqual(pf_hike_submission.map_submitter_discord.discord_id, "1234")
        self.assertEqual(
            pf_hike_submission.map_submitter_discord.discord_username, "Test1234"
        )
        self.assertEqual(pf_hike_submission.max_player_count, "8 players")
        self.assertEqual(pf_hike_submission.map, "TestMap")
        self.assertEqual(pf_hike_submission.mode, "TestMode")

        # Multiple submissions of same WAYWO post are forbidden if previous submission hasn't been playtested yet
        pbc = PathfinderBeanCount.objects.first()
        pbc.bean_count = BEAN_COST_HIKE_SUBMISSION
        pbc.save()
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": "1234",
                "mapSubmitterDiscordUsername": "Test1234",
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode": "TestModeA",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(PathfinderBeanCount.objects.count(), 1)
        self.assertEqual(PathfinderBeanCount.objects.first().bean_count, 50)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="A Pathfinder Hike submission already exists for this post.",
                code="permission_denied",
            ),
        )

        # Different submitter still blocked from submitting same WAYWO post if previous submission unplaytested
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="3456", discord_username="Test3456"
        )
        pbc = PathfinderBeanCount.objects.create(
            bean_owner_discord=discord_account,
            bean_count=BEAN_COST_HIKE_SUBMISSION,
            creator=self.user,
        )
        response = self.client.post(
            "/pathfinder/hike-submission",
            {
                "waywoPostTitle": "Test Title",
                "waywoPostId": "7890",
                "mapSubmitterDiscordId": discord_account.discord_id,
                "mapSubmitterDiscordUsername": discord_account.discord_username,
                "maxPlayerCount": "8 players",
                "map": "TestMap",
                "mode": "TestModeA",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        self.assertEqual(PathfinderHikeSubmission.objects.count(), 1)
        self.assertEqual(PathfinderBeanCount.objects.count(), 2)
        details = response.data.get("error").get("details")
        self.assertIn("detail", details)
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="A Pathfinder Hike submission already exists for this post.",
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

    def test_pathfinder_testing_lfg_post(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/testing-lfg-post", {}, format="json")
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
            "/pathfinder/testing-lfg-post",
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
            "/pathfinder/testing-lfg-post",
            {
                "posterDiscordId": "123",
                "posterDiscordUsername": "Test0123",
                "postId": "456",
                "postTitle": "Please Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        testing_lfg_post = PathfinderTestingLFGPost.objects.first()
        self.assertEqual(testing_lfg_post.poster_discord.discord_id, "123")
        self.assertEqual(testing_lfg_post.poster_discord.discord_username, "Test0123")
        self.assertEqual(testing_lfg_post.post_id, "456")
        self.assertEqual(testing_lfg_post.post_title, "Please Test")
        testing_lfg_post.delete()

    def test_pathfinder_waywo_comment(self):
        # Missing field values throw errors
        response = self.client.post("/pathfinder/waywo-comment", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "commenterDiscordId",
            "commenterDiscordUsername",
            "commentId",
            "commentLength",
            "postId",
        ]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/pathfinder/waywo-comment",
            {
                "commenterDiscordId": "abc",
                "commenterDiscordUsername": "a",
                "commentId": "abc",
                "commentLength": "abc",
                "postId": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for id_field in ["commenterDiscordId", "commentId", "postId"]:
            self.assertIn(id_field, details)
            self.assertEqual(
                details.get(id_field)[0],
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                ),
            )
        self.assertIn("commenterDiscordUsername", details)
        self.assertEqual(
            details.get("commenterDiscordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("commentLength", details)
        self.assertEqual(
            details.get("commentLength")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # Success - does not award bean as comment length is less than 100
        response = self.client.post(
            "/pathfinder/waywo-comment",
            {
                "commenterDiscordId": "123",
                "commenterDiscordUsername": "Test0123",
                "commentId": "123",
                "commentLength": 99,
                "postId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        waywo_comment = PathfinderWAYWOComment.objects.first()
        self.assertEqual(waywo_comment.commenter_discord.discord_id, "123")
        self.assertEqual(waywo_comment.commenter_discord.discord_username, "Test0123")
        self.assertEqual(waywo_comment.post_id, "456")
        self.assertEqual(waywo_comment.comment_id, "123")
        self.assertEqual(waywo_comment.comment_length, 99)
        self.assertFalse(response.data.get("awardedBean"))
        self.assertEqual(PathfinderBeanCount.objects.count(), 0)

        # Success - does not award bean as commenter is also the WAYWO post's OP
        waywo_post = PathfinderWAYWOPost.objects.create(
            post_id="456", poster_discord=discord_account, creator=self.user
        )
        response = self.client.post(
            "/pathfinder/waywo-comment",
            {
                "commenterDiscordId": "123",
                "commenterDiscordUsername": "Test0123",
                "commentId": "123",
                "commentLength": 100,
                "postId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        waywo_comment = PathfinderWAYWOComment.objects.first()
        self.assertEqual(waywo_comment.commenter_discord.discord_id, "123")
        self.assertEqual(waywo_comment.commenter_discord.discord_username, "Test0123")
        self.assertEqual(waywo_comment.post_id, "456")
        self.assertEqual(waywo_comment.comment_id, "123")
        self.assertEqual(waywo_comment.comment_length, 100)
        self.assertFalse(response.data.get("awardedBean"))
        self.assertEqual(PathfinderBeanCount.objects.count(), 0)
        waywo_comment.delete()
        waywo_post.delete()

        # Success - awards bean as it's first qualifying for the commenter on that post ID
        response = self.client.post(
            "/pathfinder/waywo-comment",
            {
                "commenterDiscordId": "123",
                "commenterDiscordUsername": "Test0123",
                "commentId": "456",
                "commentLength": 100,
                "postId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        waywo_comment = PathfinderWAYWOComment.objects.first()
        self.assertEqual(waywo_comment.commenter_discord.discord_id, "123")
        self.assertEqual(waywo_comment.commenter_discord.discord_username, "Test0123")
        self.assertEqual(waywo_comment.post_id, "456")
        self.assertEqual(waywo_comment.comment_id, "456")
        self.assertEqual(waywo_comment.comment_length, 100)
        self.assertTrue(response.data.get("awardedBean"))
        pbc = PathfinderBeanCount.objects.first()
        self.assertEqual(pbc.bean_owner_discord, discord_account)
        self.assertEqual(pbc.bean_count, BEAN_AWARD_WAYWO_COMMENT)

        # Success - does not award bean as it's not first for the commenter on that post ID
        response = self.client.post(
            "/pathfinder/waywo-comment",
            {
                "commenterDiscordId": "123",
                "commenterDiscordUsername": "Test0123",
                "commentId": "789",
                "commentLength": 106,
                "postId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        waywo_comment = PathfinderWAYWOComment.objects.first()
        self.assertEqual(waywo_comment.commenter_discord.discord_id, "123")
        self.assertEqual(waywo_comment.commenter_discord.discord_username, "Test0123")
        self.assertEqual(waywo_comment.post_id, "456")
        self.assertEqual(waywo_comment.comment_id, "789")
        self.assertEqual(waywo_comment.comment_length, 106)
        self.assertFalse(response.data.get("awardedBean"))
        pbc = PathfinderBeanCount.objects.first()
        self.assertEqual(pbc.bean_owner_discord, discord_account)
        self.assertEqual(pbc.bean_count, BEAN_AWARD_WAYWO_COMMENT)

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
    @patch("apps.pathfinder.views.get_current_era")
    def test_pathfinder_dynamo_progress_view_s3(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s3_discord_earn_dict,
        mock_get_s3_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "3"
        mock_get_current_era.return_value = None

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
    @patch("apps.pathfinder.views.get_current_era")
    def test_pathfinder_dynamo_progress_view_s4(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s4_discord_earn_dict,
        mock_get_s4_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "4"
        mock_get_current_era.return_value = None

        # TODO: Complete this test.

    @patch("apps.pathfinder.views.get_s5_xbox_earn_dict")
    @patch("apps.pathfinder.views.get_s5_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.pathfinder.views.get_current_season_id")
    @patch("apps.pathfinder.views.get_current_era")
    def test_pathfinder_dynamo_progress_view_s5(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_s5_discord_earn_dict,
        mock_get_s5_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = "5"
        mock_get_current_era.return_value = None

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

        # Exception in get_s5_discord_earn_dict throws error
        mock_get_s5_discord_earn_dict.side_effect = Exception()
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
        mock_get_s5_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s5_discord_earn_dict.side_effect = None
        mock_get_s5_discord_earn_dict.reset_mock()

        # Exception in get_s5_xbox_earn_dict throws error
        mock_get_s5_xbox_earn_dict.side_effect = Exception()
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
        mock_get_s5_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s5_xbox_earn_dict.side_effect = None
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_s5_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "bean_spender": 200,
                "what_are_you_working_on": 150,
                "feedback_fiend": 27,
            }
        }
        mock_get_s5_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "gone_hiking": 170,
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
        self.assertEqual(response.data.get("totalPoints"), 584)
        self.assertEqual(response.data.get("pointsBeanSpender"), 200)
        self.assertEqual(response.data.get("pointsWhatAreYouWorkingOn"), 150)
        self.assertEqual(response.data.get("pointsFeedbackFiend"), 27)
        self.assertEqual(response.data.get("pointsGoneHiking"), 170)
        self.assertEqual(response.data.get("pointsForgedInFire"), 37)
        mock_get_s5_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_s5_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_s5_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "bean_spender": 200,
                "what_are_you_working_on": 150,
                "feedback_fiend": 27,
            }
        }
        mock_get_s5_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "gone_hiking": 170,
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
        self.assertEqual(response.data.get("totalPoints"), 377)
        self.assertEqual(response.data.get("pointsBeanSpender"), 200)
        self.assertEqual(response.data.get("pointsWhatAreYouWorkingOn"), 150)
        self.assertEqual(response.data.get("pointsFeedbackFiend"), 27)
        self.assertEqual(response.data.get("pointsGoneHiking"), 0)
        self.assertEqual(response.data.get("pointsForgedInFire"), 0)
        mock_get_s5_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_s5_xbox_earn_dict.assert_not_called()
        mock_get_s5_discord_earn_dict.reset_mock()
        mock_get_s5_xbox_earn_dict.reset_mock()

    @patch("apps.pathfinder.views.get_e1_xbox_earn_dict")
    @patch("apps.pathfinder.views.get_e1_discord_earn_dict")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.pathfinder.views.get_current_season_id")
    @patch("apps.pathfinder.views.get_current_era")
    def test_pathfinder_dynamo_progress_view_e1(
        self,
        mock_get_current_era,
        mock_get_current_season_id,
        mock_get_xuid_and_exact_gamertag,
        mock_get_e1_discord_earn_dict,
        mock_get_e1_xbox_earn_dict,
    ):
        mock_get_current_season_id.return_value = None
        mock_get_current_era.return_value = 1

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

        # Exception in get_e1_discord_earn_dict throws error
        mock_get_e1_discord_earn_dict.side_effect = Exception()
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
        mock_get_e1_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e1_discord_earn_dict.side_effect = None
        mock_get_e1_discord_earn_dict.reset_mock()

        # Exception in get_e1_xbox_earn_dict throws error
        mock_get_e1_xbox_earn_dict.side_effect = Exception()
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
        mock_get_e1_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e1_xbox_earn_dict.side_effect = None
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

        # Success - point totals come through for all values
        mock_get_e1_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "bean_spender": 200,
                "what_are_you_working_on": 150,
                "feedback_fiend": 27,
            }
        }
        mock_get_e1_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "gone_hiking": 170,
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
        self.assertEqual(response.data.get("totalPoints"), 584)
        self.assertEqual(response.data.get("pointsBeanSpender"), 200)
        self.assertEqual(response.data.get("pointsWhatAreYouWorkingOn"), 150)
        self.assertEqual(response.data.get("pointsFeedbackFiend"), 27)
        self.assertEqual(response.data.get("pointsGoneHiking"), 170)
        self.assertEqual(response.data.get("pointsForgedInFire"), 37)
        mock_get_e1_discord_earn_dict.assert_called_once_with([link.discord_account_id])
        mock_get_e1_xbox_earn_dict.assert_called_once_with([link.xbox_live_account_id])
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

        # Success - no linked gamertag
        link.delete()
        mock_get_e1_discord_earn_dict.return_value = {
            link.discord_account_id: {
                "bean_spender": 200,
                "what_are_you_working_on": 150,
                "feedback_fiend": 27,
            }
        }
        mock_get_e1_xbox_earn_dict.return_value = {
            link.xbox_live_account_id: {
                "gone_hiking": 170,
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
        self.assertEqual(response.data.get("totalPoints"), 377)
        self.assertEqual(response.data.get("pointsBeanSpender"), 200)
        self.assertEqual(response.data.get("pointsWhatAreYouWorkingOn"), 150)
        self.assertEqual(response.data.get("pointsFeedbackFiend"), 27)
        self.assertEqual(response.data.get("pointsGoneHiking"), 0)
        self.assertEqual(response.data.get("pointsForgedInFire"), 0)
        mock_get_e1_discord_earn_dict.assert_called_once_with(
            [discord_account.discord_id]
        )
        mock_get_e1_xbox_earn_dict.assert_not_called()
        mock_get_e1_discord_earn_dict.reset_mock()
        mock_get_e1_xbox_earn_dict.reset_mock()

    @patch("apps.pathfinder.views.now_utc")
    def test_weekly_recap_view(self, mock_now_utc):
        mock_now_utc.return_value = datetime.datetime(
            year=2023,
            month=11,
            day=2,
            hour=18,
            minute=0,
            second=0,
            tzinfo=datetime.timezone.utc,
        )

        # Missing field values throw errors
        response = self.client.post("/pathfinder/weekly-recap", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUsersAwardedBeans", details)
        self.assertEqual(
            details.get("discordUsersAwardedBeans"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/pathfinder/weekly-recap",
            {
                "discordUsersAwardedBeans": [
                    {
                        "discordId": "",
                        "discordUsername": "",
                        "awardedBeans": "",
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUsersAwardedBeans", details)
        self.assertEqual(
            details.get("discordUsersAwardedBeans"),
            {
                0: {
                    "discordId": [
                        ErrorDetail(string="This field may not be blank.", code="blank")
                    ],
                    "discordUsername": [
                        ErrorDetail(string="This field may not be blank.", code="blank")
                    ],
                    "awardedBeans": [
                        ErrorDetail(
                            string="A valid integer is required.", code="invalid"
                        )
                    ],
                }
            },
        )

        # Success - returns empty data
        response = self.client.post(
            "/pathfinder/weekly-recap",
            {"discordUsersAwardedBeans": []},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("hikerCount"), 0)
        self.assertEqual(response.data.get("hikeSubmissionCount"), 0)
        self.assertEqual(response.data.get("waywoCommentCount"), 0)
        self.assertEqual(response.data.get("waywoPostCount"), 0)

        # Success - changes bean totals and returns non-empty data
        discord_account_1 = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_username="Test123"
        )
        discord_account_2 = DiscordAccount.objects.create(
            creator=self.user, discord_id="456", discord_username="Test456"
        )
        hike_submission = PathfinderHikeSubmission.objects.create(
            creator=self.user, map_submitter_discord=discord_account_1
        )
        hike_submission.created_at = datetime.datetime(
            year=2023,
            month=10,
            day=26,
            hour=18,
            minute=0,
            second=0,
            tzinfo=datetime.timezone.utc,
        )
        hike_submission.save()
        for i in range(5):
            for _ in range(2):
                game_participation = PathfinderHikeGameParticipation.objects.create(
                    creator=self.user, hike_submission=hike_submission, xuid=i
                )
                game_participation.created_at = datetime.datetime(
                    year=2023,
                    month=10,
                    day=27,
                    hour=18,
                    minute=0,
                    second=0,
                    tzinfo=datetime.timezone.utc,
                )
                game_participation.save()
        for i in range(4):
            post = PathfinderWAYWOPost.objects.create(
                creator=self.user, poster_discord=discord_account_1
            )
            post.created_at = datetime.datetime(
                year=2023,
                month=10,
                day=28,
                hour=18,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            )
            post.save()
        for i in range(3):
            comment = PathfinderWAYWOComment.objects.create(
                creator=self.user,
                comment_length=i,
                commenter_discord=discord_account_1,
            )
            comment.created_at = datetime.datetime(
                year=2023,
                month=10,
                day=29,
                hour=18,
                minute=0,
                second=0,
                tzinfo=datetime.timezone.utc,
            )
            comment.save()
        response = self.client.post(
            "/pathfinder/weekly-recap",
            {
                "discordUsersAwardedBeans": [
                    {
                        "discordId": discord_account_1.discord_id,
                        "discordUsername": discord_account_1.discord_username,
                        "awardedBeans": 15,
                    },
                    {
                        "discordId": discord_account_2.discord_id,
                        "discordUsername": discord_account_2.discord_username,
                        "awardedBeans": 25,
                    },
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("hikerCount"), 5)
        self.assertEqual(response.data.get("hikeSubmissionCount"), 1)
        self.assertEqual(response.data.get("waywoCommentCount"), 3)
        self.assertEqual(response.data.get("waywoPostCount"), 4)
        self.assertEqual(PathfinderBeanCount.objects.count(), 2)
        self.assertEqual(PathfinderBeanCount.objects.all()[0].bean_count, 25)
        self.assertEqual(
            PathfinderBeanCount.objects.all()[0].bean_owner_discord, discord_account_2
        )
        self.assertEqual(PathfinderBeanCount.objects.all()[1].bean_count, 15)
        self.assertEqual(
            PathfinderBeanCount.objects.all()[1].bean_owner_discord, discord_account_1
        )
