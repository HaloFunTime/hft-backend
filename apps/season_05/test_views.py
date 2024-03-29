import datetime
from collections import OrderedDict
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.season_05.models import (
    DomainChallengeTeamAssignment,
    DomainChallengeTeamReassignment,
    DomainMaster,
)
from apps.xbox_live.models import XboxLiveAccount


class Season05TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_check_domains_view(self, mock_get_xuid_and_exact_gamertag):
        # Missing field values throw errors
        response = self.client.post("/season-05/check-domains", {}, format="json")
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

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/check-domains",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
            },
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

        # No team assignment record returns no score info
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_username="ABC1234"
        )
        response = self.client.post(
            "/season-05/check-domains",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(DomainChallengeTeamAssignment.objects.all().count(), 0)
        self.assertEqual(response.data.get("discordUserId"), discord_account.discord_id)
        self.assertFalse(response.data.get("joinedChallenge"))
        self.assertFalse(response.data.get("linkedGamertag"))
        self.assertIsNone(response.data.get("assignedTeam"))
        self.assertEqual(response.data.get("domainsMastered"), 0)
        self.assertEqual(response.data.get("domainScores"), [])

        # Create a team assignment record (calls utility method, which returns empty list)
        DomainChallengeTeamAssignment.objects.create(
            creator=self.user,
            assignee=discord_account,
            team=DomainChallengeTeamAssignment.Teams.FunTimeBot,
        )
        response = self.client.post(
            "/season-05/check-domains",
            {
                "discordUserId": discord_account.discord_id,
                "discordUsername": discord_account.discord_username,
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), discord_account.discord_id)
        self.assertTrue(response.data.get("joinedChallenge"))
        self.assertFalse(response.data.get("linkedGamertag"))
        self.assertEqual(
            response.data.get("assignedTeam"),
            DomainChallengeTeamAssignment.Teams.FunTimeBot,
        )
        self.assertEqual(response.data.get("domainsMastered"), 0)
        self.assertEqual(response.data.get("domainScores"), [])

        # Create a Discord/Xbox Live link record (calls utility method, returns real data)
        with patch(
            "apps.season_05.views.get_domain_score_info"
        ) as mock_get_domain_score_info:
            mock_get_xuid_and_exact_gamertag.return_value = (
                2535405290989773,
                "test1234",
            )
            xbl_account = XboxLiveAccount.objects.create(
                creator=self.user, gamertag="test1234"
            )
            link = DiscordXboxLiveLink.objects.create(
                creator=self.user,
                discord_account=discord_account,
                xbox_live_account=xbl_account,
                verified=True,
            )
            mock_get_domain_score_info.return_value = [
                {
                    "name": "Test First",
                    "description": "This is description 1️⃣",
                    "effective_date": datetime.date(year=2023, month=10, day=24),
                    "current_score": 10,
                    "max_score": 10,
                    "is_mastered": True,
                },
                {
                    "name": "Test Second",
                    "description": "This is description 2️⃣",
                    "effective_date": datetime.date(year=2023, month=10, day=31),
                    "current_score": 2,
                    "max_score": 20,
                    "is_mastered": False,
                },
                {
                    "name": "Test Third",
                    "description": "This is description 3️⃣",
                    "effective_date": datetime.date(year=2023, month=11, day=7),
                    "current_score": 3,
                    "max_score": 30,
                    "is_mastered": True,
                },
            ]
            response = self.client.post(
                "/season-05/check-domains",
                {
                    "discordUserId": discord_account.discord_id,
                    "discordUsername": discord_account.discord_username,
                },
                format="json",
            )
            mock_get_domain_score_info.assert_called_once_with(link)
            self.assertEqual(
                response.data.get("discordUserId"), discord_account.discord_id
            )
            self.assertTrue(response.data.get("joinedChallenge"))
            self.assertTrue(response.data.get("linkedGamertag"))
            self.assertEqual(
                response.data.get("assignedTeam"),
                DomainChallengeTeamAssignment.Teams.FunTimeBot,
            )
            self.assertEqual(response.data.get("domainsMastered"), 2)
            self.assertEqual(
                response.data.get("domainScores"),
                [
                    OrderedDict(
                        [
                            ("name", "Test First"),
                            ("description", "This is description 1️⃣"),
                            ("effectiveDate", "2023-10-24"),
                            ("currentScore", 10),
                            ("maxScore", 10),
                            ("isMastered", True),
                        ]
                    ),
                    OrderedDict(
                        [
                            ("name", "Test Second"),
                            ("description", "This is description 2️⃣"),
                            ("effectiveDate", "2023-10-31"),
                            ("currentScore", 2),
                            ("maxScore", 20),
                            ("isMastered", False),
                        ]
                    ),
                    OrderedDict(
                        [
                            ("name", "Test Third"),
                            ("description", "This is description 3️⃣"),
                            ("effectiveDate", "2023-11-07"),
                            ("currentScore", 3),
                            ("maxScore", 30),
                            ("isMastered", True),
                        ]
                    ),
                ],
            )

    @patch("apps.season_05.views.sleep")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_check_teams_view(self, mock_get_xuid_and_exact_gamertag, mock_sleep):
        # No team assignment record returns no score info
        response = self.client.get("/season-05/check-teams")
        self.assertEqual(response.data.get("teamScores"), [])

        with patch(
            "apps.season_05.views.get_domain_score_info"
        ) as mock_get_domain_score_info:
            mock_get_domain_score_info.return_value = []
            # Create a linked team assignment record for Team FunTimeBot
            discord_account_a = DiscordAccount.objects.create(
                creator=self.user, discord_id="123", discord_username="ABC1234"
            )
            mock_get_xuid_and_exact_gamertag.return_value = (
                0,
                "test1234",
            )
            xbl_account_a = XboxLiveAccount.objects.create(
                creator=self.user, gamertag="test1234"
            )
            DiscordXboxLiveLink.objects.create(
                creator=self.user,
                discord_account=discord_account_a,
                xbox_live_account=xbl_account_a,
                verified=True,
            )
            DomainChallengeTeamAssignment.objects.create(
                creator=self.user,
                assignee=discord_account_a,
                team=DomainChallengeTeamAssignment.Teams.FunTimeBot,
            )
            response = self.client.get("/season-05/check-teams")
            self.assertEqual(
                response.data.get("teamScores"),
                [{"team": "FunTimeBot", "memberCount": 1, "domainsMastered": 0}],
            )
            # Create a linked team assignment record for Team HFT Intern
            discord_account_b = DiscordAccount.objects.create(
                creator=self.user, discord_id="456", discord_username="DEF1234"
            )
            mock_get_xuid_and_exact_gamertag.return_value = (
                1,
                "test5678",
            )
            xbl_account_b = XboxLiveAccount.objects.create(
                creator=self.user, gamertag="test5678"
            )
            DiscordXboxLiveLink.objects.create(
                creator=self.user,
                discord_account=discord_account_b,
                xbox_live_account=xbl_account_b,
                verified=True,
            )
            DomainChallengeTeamAssignment.objects.create(
                creator=self.user,
                assignee=discord_account_b,
                team=DomainChallengeTeamAssignment.Teams.HFT_Intern,
            )
            response = self.client.get("/season-05/check-teams")
            self.assertEqual(
                response.data.get("teamScores"),
                [
                    OrderedDict(
                        [
                            ("team", "FunTimeBot"),
                            ("memberCount", 1),
                            ("domainsMastered", 0),
                        ]
                    ),
                    OrderedDict(
                        [
                            ("team", "HFT Intern"),
                            ("memberCount", 1),
                            ("domainsMastered", 0),
                        ]
                    ),
                ],
            )

            # Add two masteries in there
            mock_get_domain_score_info.return_value = [
                {
                    "name": "Test First",
                    "description": "This is description 1️⃣",
                    "effective_date": datetime.date(year=2023, month=10, day=24),
                    "current_score": 10,
                    "max_score": 10,
                    "is_mastered": True,
                },
                {
                    "name": "Test Second",
                    "description": "This is description 2️⃣",
                    "effective_date": datetime.date(year=2023, month=10, day=31),
                    "current_score": 2,
                    "max_score": 20,
                    "is_mastered": False,
                },
                {
                    "name": "Test Third",
                    "description": "This is description 3️⃣",
                    "effective_date": datetime.date(year=2023, month=11, day=7),
                    "current_score": 3,
                    "max_score": 30,
                    "is_mastered": True,
                },
            ]
            response = self.client.get("/season-05/check-teams")
            self.assertEqual(
                response.data.get("teamScores"),
                [
                    OrderedDict(
                        [
                            ("team", "FunTimeBot"),
                            ("memberCount", 1),
                            ("domainsMastered", 2),
                        ]
                    ),
                    OrderedDict(
                        [
                            ("team", "HFT Intern"),
                            ("memberCount", 1),
                            ("domainsMastered", 2),
                        ]
                    ),
                ],
            )
        mock_sleep.assert_not_called()

    def test_join_challenge_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-05/join-challenge", {}, format="json")
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

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
            },
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

        # New assignment
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(DomainChallengeTeamAssignment.objects.all().count(), 1)
        assignment_record = DomainChallengeTeamAssignment.objects.first()
        self.assertEqual(assignment_record.assignee_id, "123")
        self.assertIsNotNone(assignment_record.team)
        self.assertIsNotNone(response.data.get("assignedTeam"))
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), True)
        initial_team = assignment_record.team

        # Existing assignment
        response = self.client.post(
            "/season-05/join-challenge",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(DomainChallengeTeamAssignment.objects.all().count(), 1)
        assignment_record = DomainChallengeTeamAssignment.objects.first()
        self.assertEqual(assignment_record.assignee_id, "123")
        self.assertIsNotNone(assignment_record.team)
        self.assertEqual(response.data.get("assignedTeam"), initial_team)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), False)

    def test_process_reassignments_view(self):
        # Missing field values throw errors
        response = self.client.post(
            "/season-05/process-reassignments", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("date", details)
        self.assertEqual(
            details.get("date"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/process-reassignments", {"date": "abc"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("date", details)
        self.assertEqual(
            details.get("date")[0],
            ErrorDetail(
                string="Date has wrong format. Use one of these formats instead: YYYY-MM-DD.",
                code="invalid",
            ),
        )

        # Success - nothing to process
        response = self.client.post(
            "/season-05/process-reassignments", {"date": "2023-10-17"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("date"), "2023-10-17")
        self.assertEqual(response.data.get("processedReassignments"), [])

        # Success - processes 5 reassignments 2023/10/17, 5 more 2023/10/24
        for i in range(5):
            discord_account = DiscordAccount.objects.create(
                creator=self.user, discord_id=str(i), discord_username=f"ABC{i}"
            )
            DomainChallengeTeamAssignment.objects.create(
                creator=self.user,
                assignee=discord_account,
                team=DomainChallengeTeamAssignment.Teams.FunTimeBot,
            )
            DomainChallengeTeamReassignment.objects.create(
                creator=self.user,
                reassignee=discord_account,
                next_team=DomainChallengeTeamAssignment.Teams.HFT_Intern,
                reassignment_date=datetime.date(year=2023, month=10, day=17),
                reason=f"Reason{i}",
            )
            DomainChallengeTeamReassignment.objects.create(
                creator=self.user,
                reassignee=discord_account,
                next_team=DomainChallengeTeamAssignment.Teams.Unassigned,
                reassignment_date=datetime.date(year=2023, month=10, day=24),
                reason=f"Reason{i}",
            )
        response = self.client.post(
            "/season-05/process-reassignments", {"date": "2023-10-17"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("date"), "2023-10-17")
        self.assertEqual(
            response.data.get("processedReassignments"),
            [
                OrderedDict(
                    [
                        ("discordUserId", "4"),
                        ("team", "HFT Intern"),
                        ("reason", "Reason4"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "3"),
                        ("team", "HFT Intern"),
                        ("reason", "Reason3"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "2"),
                        ("team", "HFT Intern"),
                        ("reason", "Reason2"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "1"),
                        ("team", "HFT Intern"),
                        ("reason", "Reason1"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "0"),
                        ("team", "HFT Intern"),
                        ("reason", "Reason0"),
                    ]
                ),
            ],
        )
        self.assertEqual(DomainChallengeTeamReassignment.objects.count(), 5)
        response = self.client.post(
            "/season-05/process-reassignments", {"date": "2023-10-24"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("date"), "2023-10-24")
        self.assertEqual(
            response.data.get("processedReassignments"),
            [
                OrderedDict(
                    [
                        ("discordUserId", "4"),
                        ("team", "Unassigned"),
                        ("reason", "Reason4"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "3"),
                        ("team", "Unassigned"),
                        ("reason", "Reason3"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "2"),
                        ("team", "Unassigned"),
                        ("reason", "Reason2"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "1"),
                        ("team", "Unassigned"),
                        ("reason", "Reason1"),
                    ]
                ),
                OrderedDict(
                    [
                        ("discordUserId", "0"),
                        ("team", "Unassigned"),
                        ("reason", "Reason0"),
                    ]
                ),
            ],
        )
        self.assertEqual(DomainChallengeTeamReassignment.objects.count(), 0)

    def test_save_master_view(self):
        # Missing field values throw errors
        response = self.client.post("/season-05/save-master", {}, format="json")
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
        self.assertIn("domainsMastered", details)
        self.assertEqual(
            details.get("domainsMastered"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "domainsMastered": "not_an_int",
            },
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
        self.assertIn("domainsMastered", details)
        self.assertEqual(
            details.get("domainsMastered")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New master
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "domainsMastered": 10,
            },
            format="json",
        )
        self.assertEqual(DomainMaster.objects.all().count(), 1)
        master_record = DomainMaster.objects.first()
        self.assertEqual(master_record.master_id, "123")
        self.assertGreaterEqual(master_record.mastered_at, now_before_post)
        self.assertEqual(master_record.domain_count, 10)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMaster"), True)
        initial_mastered_at = master_record.mastered_at

        # Existing master, domain count update
        response = self.client.post(
            "/season-05/save-master",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "domainsMastered": 11,
            },
            format="json",
        )
        self.assertEqual(DomainMaster.objects.all().count(), 1)
        master_record = DomainMaster.objects.first()
        self.assertEqual(master_record.master_id, "123")
        self.assertGreaterEqual(master_record.mastered_at, initial_mastered_at)
        self.assertEqual(master_record.domain_count, 11)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newMaster"), False)
