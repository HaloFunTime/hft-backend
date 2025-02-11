import datetime
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.era_03.models import (
    BoatAssignment,
    BoatCaptain,
    BoatDeckhand,
    BoatRank,
    WeeklyBoatAssignments,
)
from apps.halo_infinite.models import HaloInfiniteMatch
from apps.link.models import DiscordXboxLiveLink
from apps.xbox_live.models import XboxLiveAccount


class Era03TestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)
        self.first_rank = BoatRank.objects.create(
            creator=self.user,
            rank="Junior Deckhand",
            tier=1,
            track="N/A",
            description="The lowest rank in the crew. Responsible for sweeping the poop deck.",
        )
        self.second_rank = BoatRank.objects.create(
            creator=self.user,
            rank="Test Rank 2 Name",
            tier=2,
            track="N/A",
            description="The second-lowest rank in the crew. Responsible for sweeping the poop deck.",
        )
        self.max_rank = BoatRank.objects.create(
            creator=self.user,
            rank="Test Rank 10 Name",
            tier=10,
            track="N/A",
            description="The highest rank in the crew. Still responsible for sweeping the poop deck.",
        )

    def test_board_boat_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/board-boat", {}, format="json")
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
            "/era-03/board-boat",
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

        # New deckhand
        response = self.client.post(
            "/era-03/board-boat",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), True)
        self.assertEqual(response.data.get("rank"), "Junior Deckhand")
        self.assertEqual(BoatDeckhand.objects.all().count(), 1)
        deckhand_record = BoatDeckhand.objects.first()
        self.assertEqual(deckhand_record.deckhand_id, "123")
        self.assertEqual(deckhand_record.rank, self.first_rank)

        # Existing deckhand
        response = self.client.post(
            "/era-03/board-boat",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newJoiner"), False)
        self.assertEqual(response.data.get("rank"), "Junior Deckhand")
        self.assertEqual(BoatDeckhand.objects.all().count(), 1)
        deckhand_record = BoatDeckhand.objects.first()
        self.assertEqual(deckhand_record.deckhand_id, "123")
        self.assertEqual(deckhand_record.rank, self.first_rank)

    @patch("apps.halo_infinite.signals.match_stats")
    @patch("apps.era_03.views.check_xuid_assignment")
    @patch("apps.era_03.views.generate_weekly_assignments")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    @patch("apps.era_03.views.get_current_week_start")
    def test_check_boat_assignments_view(
        self,
        mock_get_current_week_start,
        mock_get_xuid_and_exact_gamertag,
        mock_generate_weekly_assignments,
        mock_check_xuid_assignment,
        mock_match_stats,
    ):
        mock_get_current_week_start.return_value = datetime.date(2025, 2, 11)

        # Missing field values throw errors
        response = self.client.post("/era-03/check-boat-assignments", {}, format="json")
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
            "/era-03/check-boat-assignments",
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

        # Early return - has not joined challenge
        test_discord_user = DiscordAccount.objects.create(
            discord_id="123",
            discord_username="test123",
            creator=self.user,
        )
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), False)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("currentRank"), "N/A")
        self.assertEqual(response.data.get("currentRankTier"), 0)
        self.assertEqual(response.data.get("assignment1"), None)
        self.assertEqual(response.data.get("assignment1Completed"), False)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), False)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), False)
        self.assertEqual(response.data.get("assignmentsCompleted"), False)
        self.assertEqual(response.data.get("existingAssignments"), False)
        self.assertEqual(response.data.get("justPromoted"), False)

        # Early return - has not linked gamertag
        test_deckhand = BoatDeckhand.objects.create(
            deckhand=test_discord_user,
            rank=self.first_rank,
            creator=self.user,
        )
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), False)
        self.assertEqual(response.data.get("currentRank"), "N/A")
        self.assertEqual(response.data.get("currentRankTier"), 0)
        self.assertEqual(response.data.get("assignment1"), None)
        self.assertEqual(response.data.get("assignment1Completed"), False)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), False)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), False)
        self.assertEqual(response.data.get("assignmentsCompleted"), False)
        self.assertEqual(response.data.get("existingAssignments"), False)
        self.assertEqual(response.data.get("justPromoted"), False)

        # Early return - already at rank 10
        mock_get_xuid_and_exact_gamertag.return_value = (123, "Test123")
        test_xbox_live_account = XboxLiveAccount.objects.create(
            gamertag="test123",
            creator=self.user,
        )
        DiscordXboxLiveLink.objects.create(
            discord_account=test_discord_user,
            xbox_live_account=test_xbox_live_account,
            verified=True,
            creator=self.user,
        )
        test_deckhand.rank = self.max_rank
        test_deckhand.save()
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("currentRank"), "Test Rank 10 Name")
        self.assertEqual(response.data.get("currentRankTier"), 10)
        self.assertEqual(response.data.get("assignment1"), None)
        self.assertEqual(response.data.get("assignment1Completed"), False)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), False)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), False)
        self.assertEqual(response.data.get("assignmentsCompleted"), False)
        self.assertEqual(response.data.get("existingAssignments"), False)
        self.assertEqual(response.data.get("justPromoted"), False)

        # Early return - newly-created assignments
        test_deckhand.rank = self.first_rank
        test_deckhand.save()
        mock_generate_weekly_assignments.side_effect = (
            lambda x, y, z: WeeklyBoatAssignments.objects.create(
                deckhand=x,
                week_start=y,
                assignment_1=BoatAssignment.objects.create(
                    description="Test Assignment 1",
                    creator=self.user,
                ),
                next_rank=self.second_rank,
                creator=z,
            )
        )
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("currentRank"), "Junior Deckhand")
        self.assertEqual(response.data.get("currentRankTier"), 1)
        self.assertEqual(response.data.get("assignment1"), "Test Assignment 1")
        self.assertEqual(response.data.get("assignment1Completed"), False)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), False)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), False)
        self.assertEqual(response.data.get("assignmentsCompleted"), False)
        self.assertEqual(response.data.get("existingAssignments"), False)
        self.assertEqual(response.data.get("justPromoted"), False)
        mock_generate_weekly_assignments.assert_called_once_with(
            test_deckhand,
            datetime.date(2025, 2, 11),
            self.user,
        )
        mock_check_xuid_assignment.assert_not_called()
        self.assertEqual(WeeklyBoatAssignments.objects.all().count(), 1)
        weekly_assignments = WeeklyBoatAssignments.objects.first()
        self.assertEqual(weekly_assignments.deckhand, test_deckhand)
        self.assertEqual(weekly_assignments.week_start, datetime.date(2025, 2, 11))
        self.assertEqual(
            weekly_assignments.assignment_1.description, "Test Assignment 1"
        )
        self.assertEqual(weekly_assignments.next_rank, self.second_rank)
        self.assertEqual(weekly_assignments.creator, self.user)

        # Early return - assignments are incomplete
        mock_check_xuid_assignment.side_effect = [
            None,
            None,
            None,
        ]
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("currentRank"), "Junior Deckhand")
        self.assertEqual(response.data.get("currentRankTier"), 1)
        self.assertEqual(response.data.get("assignment1"), "Test Assignment 1")
        self.assertEqual(response.data.get("assignment1Completed"), False)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), True)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), True)
        self.assertEqual(response.data.get("assignmentsCompleted"), False)
        self.assertEqual(response.data.get("existingAssignments"), True)
        self.assertEqual(response.data.get("justPromoted"), False)
        mock_check_xuid_assignment.assert_called_once_with(
            test_xbox_live_account.xuid,
            weekly_assignments.assignment_1,
            datetime.date(2025, 2, 11),
        )
        mock_check_xuid_assignment.reset_mock()

        # Early return - already promoted this week
        test_deckhand.rank = self.second_rank
        test_deckhand.save()
        test_match_id = uuid.uuid4()
        mock_match_stats.return_value = {
            "MatchId": str(test_match_id),
            "MatchInfo": {
                "StartTime": "2025-02-11T00:00:00Z",
                "EndTime": "2025-02-11T00:00:00Z",
            },
        }
        test_match = HaloInfiniteMatch.objects.create(
            match_id=test_match_id,
            creator=self.user,
        )
        mock_check_xuid_assignment.side_effect = [
            test_match,
            None,
            None,
        ]
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("currentRank"), "Test Rank 2 Name")
        self.assertEqual(response.data.get("currentRankTier"), 2)
        self.assertEqual(response.data.get("assignment1"), "Test Assignment 1")
        self.assertEqual(response.data.get("assignment1Completed"), True)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), True)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), True)
        self.assertEqual(response.data.get("assignmentsCompleted"), True)
        self.assertEqual(response.data.get("existingAssignments"), True)
        self.assertEqual(response.data.get("justPromoted"), False)
        mock_check_xuid_assignment.assert_called_once_with(
            test_xbox_live_account.xuid,
            weekly_assignments.assignment_1,
            datetime.date(2025, 2, 11),
        )
        mock_check_xuid_assignment.reset_mock()
        weekly_assignments.refresh_from_db()
        self.assertEqual(
            str(weekly_assignments.assignment_1_completion_match_id),
            test_match.match_id,
        )
        weekly_assignments.assignment_1_completion_match_id = None
        weekly_assignments.save()

        # Happy path - deckhand has completed all assignments for the week and just earned a promotion
        test_deckhand.rank = self.first_rank
        test_deckhand.save()
        mock_check_xuid_assignment.side_effect = [
            test_match,
            None,
            None,
        ]
        response = self.client.post(
            "/era-03/check-boat-assignments",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("joinedChallenge"), True)
        self.assertEqual(response.data.get("linkedGamertag"), True)
        self.assertEqual(response.data.get("currentRank"), "Test Rank 2 Name")
        self.assertEqual(response.data.get("currentRankTier"), 2)
        self.assertEqual(response.data.get("assignment1"), "Test Assignment 1")
        self.assertEqual(response.data.get("assignment1Completed"), True)
        self.assertEqual(response.data.get("assignment2"), None)
        self.assertEqual(response.data.get("assignment2Completed"), True)
        self.assertEqual(response.data.get("assignment3"), None)
        self.assertEqual(response.data.get("assignment3Completed"), True)
        self.assertEqual(response.data.get("assignmentsCompleted"), True)
        self.assertEqual(response.data.get("existingAssignments"), True)
        self.assertEqual(response.data.get("justPromoted"), True)
        mock_check_xuid_assignment.assert_called_once_with(
            test_xbox_live_account.xuid,
            weekly_assignments.assignment_1,
            datetime.date(2025, 2, 11),
        )
        mock_check_xuid_assignment.reset_mock()
        weekly_assignments.refresh_from_db()
        self.assertEqual(
            str(weekly_assignments.assignment_1_completion_match_id),
            test_match.match_id,
        )
        self.assertEqual(weekly_assignments.completed_all_assignments, True)
        test_deckhand.refresh_from_db()
        self.assertEqual(test_deckhand.rank, self.second_rank)

    def test_save_captain_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/save-boat-captain", {}, format="json")
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
        self.assertIn("rankTier", details)
        self.assertEqual(
            details.get("rankTier"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
                "rankTier": "not_an_int",
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
        self.assertIn("rankTier", details)
        self.assertEqual(
            details.get("rankTier")[0],
            ErrorDetail(
                string="A valid integer is required.",
                code="invalid",
            ),
        )

        # New captain
        now_before_post = datetime.datetime.now(tz=datetime.timezone.utc)
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
                "rankTier": 3,
            },
            format="json",
        )
        self.assertEqual(BoatCaptain.objects.all().count(), 1)
        captain_record = BoatCaptain.objects.first()
        self.assertEqual(captain_record.earner_id, "123")
        self.assertGreaterEqual(captain_record.earned_at, now_before_post)
        self.assertEqual(captain_record.rank_tier, 3)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBoatCaptain"), True)
        initial_earned_at = captain_record.earned_at

        # Existing captain, rank tier update
        response = self.client.post(
            "/era-03/save-boat-captain",
            {
                "discordUserId": "123",
                "discordUsername": "test1234",
                "rankTier": 4,
            },
            format="json",
        )
        self.assertEqual(BoatCaptain.objects.all().count(), 1)
        captain_record = BoatCaptain.objects.first()
        self.assertEqual(captain_record.earner_id, "123")
        self.assertGreaterEqual(captain_record.earned_at, initial_earned_at)
        self.assertEqual(captain_record.rank_tier, 4)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("newBoatCaptain"), False)

    def test_check_deckhand_games_view(self):
        # Missing field values throw errors
        response = self.client.post("/era-03/check-deckhand-games", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/era-03/check-deckhand-games",
            {
                "discordUserIds": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserIds", details)
        self.assertEqual(
            details.get("discordUserIds")[0],
            ErrorDetail(
                string='Expected a list of items but got type "str".', code="not_a_list"
            ),
        )

        # TODO: Test the rest... or not
