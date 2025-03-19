import datetime
import random
import uuid
from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.era_03.models import (
    BoatAssignment,
    BoatCaptain,
    BoatDeckhand,
    BoatRank,
    BoatSecret,
    BoatSecretUnlock,
    WeeklyBoatAssignments,
)
from apps.era_03.utils import (
    EARLIEST_TIME,
    LATEST_TIME,
    check_deckhand_promotion,
    fetch_match_ids_for_xuid,
    generate_weekly_assignments,
    save_new_matches,
)
from apps.halo_infinite.models import HaloInfiniteMatch


class Era03TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_boat_captain_save(self):
        # Creating a BoatCaptain record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        boat_captain = BoatCaptain.objects.create(
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
            rank_tier=1,
        )
        self.assertEqual(boat_captain.creator, self.user)
        self.assertEqual(boat_captain.earner_id, discord_account.discord_id)
        self.assertEqual(
            boat_captain.earned_at,
            datetime.datetime(2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(discord_account.boat_captain, boat_captain)

        # Duplicate BoatCaptain record (same `earner`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "BoatCaptain_earner_id_key"\n'
            + "DETAIL:  Key (earner_id)=(test) already exists.\n",
            BoatCaptain.objects.create,
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 7, 7, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
            rank_tier=1,
        )


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        self.discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id=123, discord_username="Test123"
        )

    @patch("apps.era_03.utils.matches_between")
    def test_fetch_match_ids_for_xuid(self, mock_matches_between):
        # With no data
        mock_matches_between.return_value = []
        match_ids = fetch_match_ids_for_xuid(123)
        mock_matches_between.assert_called_once_with(
            123, EARLIEST_TIME, LATEST_TIME, session=None, ids_only=True
        )
        self.assertEqual(match_ids, [])
        mock_matches_between.reset_mock()

        # Test with data
        mock_matches_between.return_value = [
            {
                "MatchId": "test1",
                "MatchInfo": {
                    "StartTime": "2023-01-02T07:50:24.936Z",
                    "EndTime": "2023-01-02T08:06:04.702Z",
                    "Duration": "PT15M18.2160311S",
                    "MapVariant": {},
                    "UgcGameVariant": {},
                    "Playlist": {},
                },
                "Outcome": 2,
                "Rank": 1,
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchId": "test2",
                "MatchInfo": {
                    "StartTime": "2023-01-01T20:30:35.9Z",
                    "EndTime": "2023-01-01T20:46:14.302Z",
                    "Duration": "PT15M18.2009991S",
                    "MapVariant": {},
                    "UgcGameVariant": {},
                    "Playlist": {},
                },
                "Outcome": 2,
                "Rank": 1,
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchId": "test3",
                "MatchInfo": {
                    "StartTime": "2022-12-30T05:09:18.875Z",
                    "EndTime": "2022-12-30T05:18:30.758Z",
                    "Duration": "PT8M37.3625903S",
                    "MapVariant": {},
                    "UgcGameVariant": {},
                    "Playlist": {},
                },
                "Outcome": 3,
                "Rank": 12,
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchId": "test4",
                "MatchInfo": {
                    "StartTime": "2022-12-30T05:01:15.609Z",
                    "EndTime": "2022-12-30T05:07:50.548Z",
                    "Duration": "PT6M2.8487807S",
                    "MapVariant": {},
                    "UgcGameVariant": {},
                    "Playlist": {},
                },
                "Outcome": 3,
                "Rank": 7,
                "PresentAtEndOfMatch": True,
            },
            {
                "MatchId": "90bd95ab-ea56-4f85-96ca-3c1aafc85cf1",
                "MatchInfo": {
                    "StartTime": "2022-11-30T04:47:20.552Z",
                    "EndTime": "2022-11-30T04:59:32.674Z",
                    "Duration": "PT11M40.0166266S",
                    "MapVariant": {},
                    "UgcGameVariant": {},
                    "Playlist": {},
                },
                "Outcome": 3,
                "Rank": 8,
                "PresentAtEndOfMatch": True,
            },
        ]
        match_ids = fetch_match_ids_for_xuid(456)
        mock_matches_between.assert_called_once_with(
            456, EARLIEST_TIME, LATEST_TIME, session=None, ids_only=True
        )
        self.assertEqual(
            match_ids,
            [
                "test1",
                "test2",
                "test3",
                "test4",
                "90bd95ab-ea56-4f85-96ca-3c1aafc85cf1",
            ],
        )

    def test_generate_weekly_assignments(self):
        tier1 = BoatRank.objects.create(creator=self.user, rank="Test1", tier=1)
        tier2 = BoatRank.objects.create(creator=self.user, rank="Test2", tier=2)
        tier3 = BoatRank.objects.create(creator=self.user, rank="Test3", tier=3)
        tier4 = BoatRank.objects.create(creator=self.user, rank="Test4", tier=4)
        tier5 = BoatRank.objects.create(creator=self.user, rank="Test5", tier=5)
        tier6 = BoatRank.objects.create(creator=self.user, rank="Test6", tier=6)
        tier7command = BoatRank.objects.create(
            creator=self.user, rank="Command7", tier=7, track=BoatRank.Tracks.COMMAND
        )
        tier7culinary = BoatRank.objects.create(
            creator=self.user, rank="Culinary7", tier=7, track=BoatRank.Tracks.CULINARY
        )
        tier7machinery = BoatRank.objects.create(
            creator=self.user,
            rank="Machinery7",
            tier=7,
            track=BoatRank.Tracks.MACHINERY,
        )
        tier7hospitality = BoatRank.objects.create(
            creator=self.user,
            rank="Hospitality7",
            tier=7,
            track=BoatRank.Tracks.HOSPITALITY,
        )
        tier8command = BoatRank.objects.create(
            creator=self.user, rank="Command8", tier=8, track=BoatRank.Tracks.COMMAND
        )
        tier8culinary = BoatRank.objects.create(
            creator=self.user, rank="Culinary8", tier=8, track=BoatRank.Tracks.CULINARY
        )
        tier8machinery = BoatRank.objects.create(
            creator=self.user,
            rank="Machinery8",
            tier=8,
            track=BoatRank.Tracks.MACHINERY,
        )
        tier8hospitality = BoatRank.objects.create(
            creator=self.user,
            rank="Hospitality8",
            tier=8,
            track=BoatRank.Tracks.HOSPITALITY,
        )
        tier9command = BoatRank.objects.create(
            creator=self.user, rank="Command9", tier=9, track=BoatRank.Tracks.COMMAND
        )
        tier9culinary = BoatRank.objects.create(
            creator=self.user, rank="Culinary9", tier=9, track=BoatRank.Tracks.CULINARY
        )
        tier9machinery = BoatRank.objects.create(
            creator=self.user,
            rank="Machinery9",
            tier=9,
            track=BoatRank.Tracks.MACHINERY,
        )
        tier9hospitality = BoatRank.objects.create(
            creator=self.user,
            rank="Hospitality9",
            tier=9,
            track=BoatRank.Tracks.HOSPITALITY,
        )
        tier10 = BoatRank.objects.create(creator=self.user, rank="Test10", tier=10)
        ranks_by_tier_and_track = {
            7: {
                BoatRank.Tracks.COMMAND: tier7command,
                BoatRank.Tracks.CULINARY: tier7culinary,
                BoatRank.Tracks.MACHINERY: tier7machinery,
                BoatRank.Tracks.HOSPITALITY: tier7hospitality,
            },
            8: {
                BoatRank.Tracks.COMMAND: tier8command,
                BoatRank.Tracks.CULINARY: tier8culinary,
                BoatRank.Tracks.MACHINERY: tier8machinery,
                BoatRank.Tracks.HOSPITALITY: tier8hospitality,
            },
            9: {
                BoatRank.Tracks.COMMAND: tier9command,
                BoatRank.Tracks.CULINARY: tier9culinary,
                BoatRank.Tracks.MACHINERY: tier9machinery,
                BoatRank.Tracks.HOSPITALITY: tier9hospitality,
            },
        }

        easy1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.EASY,
            description="Easy1",
        )
        easy2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.EASY,
            description="Easy2",
        )
        easy3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.EASY,
            description="Easy3",
        )
        easy_assignments = [easy1, easy2, easy3]
        medium1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MEDIUM,
            description="Medium1",
        )
        medium2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MEDIUM,
            description="Medium2",
        )
        medium3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MEDIUM,
            description="Medium3",
        )
        medium_assignments = [medium1, medium2, medium3]
        hard1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HARD,
            description="Hard1",
        )
        hard2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HARD,
            description="Hard2",
        )
        hard3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HARD,
            description="Hard3",
        )
        hard_assignments = [hard1, hard2, hard3]
        command1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.COMMAND,
            description="Command1",
        )
        command2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.COMMAND,
            description="Command2",
        )
        command3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.COMMAND,
            description="Command3",
        )
        command_assignments = [command1, command2, command3]
        culinary1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.CULINARY,
            description="Culinary1",
        )
        culinary2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.CULINARY,
            description="Culinary2",
        )
        culinary3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.CULINARY,
            description="Culinary3",
        )
        culinary_assignments = [culinary1, culinary2, culinary3]
        hospitality1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HOSPITALITY,
            description="Hospitality1",
        )
        hospitality2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HOSPITALITY,
            description="Hospitality2",
        )
        hospitality3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.HOSPITALITY,
            description="Hospitality3",
        )
        hospitality_assignments = [hospitality1, hospitality2, hospitality3]
        machinery1 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MACHINERY,
            description="Machinery1",
        )
        machinery2 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MACHINERY,
            description="Machinery2",
        )
        machinery3 = BoatAssignment.objects.create(
            creator=self.user,
            classification=BoatAssignment.Classification.MACHINERY,
            description="Machinery3",
        )
        machinery_assignments = [machinery1, machinery2, machinery3]
        assignments_by_track = {
            BoatRank.Tracks.COMMAND: command_assignments,
            BoatRank.Tracks.CULINARY: culinary_assignments,
            BoatRank.Tracks.MACHINERY: machinery_assignments,
            BoatRank.Tracks.HOSPITALITY: hospitality_assignments,
        }

        deckhand = BoatDeckhand.objects.create(
            creator=self.user,
            deckhand_id=self.discord_account.discord_id,
            rank=tier1,
        )

        # Rank 1 generates 1 easy assignment
        deckhand.rank = tier1
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNone(weekly_assignments.assignment_2)
        self.assertIsNone(weekly_assignments.assignment_3)
        # Assignment 1 is an easy assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.EASY,
        )
        self.assertIn(weekly_assignments.assignment_1, easy_assignments)
        # Next rank is tier 2
        self.assertEqual(weekly_assignments.next_rank, tier2)

        # Rank 2 generates 2 easy assignments
        deckhand.rank = tier2
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNotNone(weekly_assignments.assignment_2)
        self.assertIsNone(weekly_assignments.assignment_3)
        # Assignment 1 is an easy assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.EASY,
        )
        self.assertIn(weekly_assignments.assignment_1, easy_assignments)
        # Assignment 2 is an easy assignment
        self.assertEqual(
            weekly_assignments.assignment_2.classification,
            BoatAssignment.Classification.EASY,
        )
        self.assertIn(weekly_assignments.assignment_2, easy_assignments)
        # Assignment 1 and 2 are different
        self.assertNotEqual(
            weekly_assignments.assignment_1, weekly_assignments.assignment_2
        )
        # Next rank is tier 3
        self.assertEqual(weekly_assignments.next_rank, tier3)

        # Rank 3 generates 1 easy and 1 medium assignment
        deckhand.rank = tier3
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNotNone(weekly_assignments.assignment_2)
        self.assertIsNone(weekly_assignments.assignment_3)
        # Assignment 1 is an easy assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.EASY,
        )
        self.assertIn(weekly_assignments.assignment_1, easy_assignments)
        # Assignment 2 is a medium assignment
        self.assertEqual(
            weekly_assignments.assignment_2.classification,
            BoatAssignment.Classification.MEDIUM,
        )
        self.assertIn(weekly_assignments.assignment_2, medium_assignments)
        # Next rank is tier 4
        self.assertEqual(weekly_assignments.next_rank, tier4)

        # Rank 4 generates 2 medium assignments (no duplicates)
        deckhand.rank = tier4
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNotNone(weekly_assignments.assignment_2)
        self.assertIsNone(weekly_assignments.assignment_3)
        # Assignment 1 is a medium assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.MEDIUM,
        )
        self.assertIn(weekly_assignments.assignment_1, medium_assignments)
        # Assignment 2 is a medium assignment
        self.assertEqual(
            weekly_assignments.assignment_2.classification,
            BoatAssignment.Classification.MEDIUM,
        )
        self.assertIn(weekly_assignments.assignment_2, medium_assignments)
        # Assignment 1 and 2 are different
        self.assertNotEqual(
            weekly_assignments.assignment_1, weekly_assignments.assignment_2
        )
        # Next rank is tier 5
        self.assertEqual(weekly_assignments.next_rank, tier5)

        # Rank 5 generates 1 easy, 1 medium, and 1 hard assignment
        deckhand.rank = tier5
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNotNone(weekly_assignments.assignment_2)
        self.assertIsNotNone(weekly_assignments.assignment_3)
        # Assignment 1 is an easy assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.EASY,
        )
        self.assertIn(weekly_assignments.assignment_1, easy_assignments)
        # Assignment 2 is a medium assignment
        self.assertEqual(
            weekly_assignments.assignment_2.classification,
            BoatAssignment.Classification.MEDIUM,
        )
        self.assertIn(weekly_assignments.assignment_2, medium_assignments)
        # Assignment 3 is a hard assignment
        self.assertEqual(
            weekly_assignments.assignment_3.classification,
            BoatAssignment.Classification.HARD,
        )
        self.assertIn(weekly_assignments.assignment_3, hard_assignments)
        # Next rank is tier 6
        self.assertEqual(weekly_assignments.next_rank, tier6)

        # Rank 6 generates 1 medium and 1 from a randomized track
        deckhand.rank = tier6
        deckhand.save()
        weekly_assignments = generate_weekly_assignments(
            deckhand, datetime.date(2025, 1, 1), self.user
        )
        # Correct assignments are generated
        self.assertIsNotNone(weekly_assignments.assignment_1)
        self.assertIsNotNone(weekly_assignments.assignment_2)
        self.assertIsNone(weekly_assignments.assignment_3)
        # Next rank is tier 7
        self.assertEqual(weekly_assignments.next_rank.tier, 7)
        next_rank_track = weekly_assignments.next_rank.track
        self.assertEqual(
            weekly_assignments.next_rank, ranks_by_tier_and_track[7][next_rank_track]
        )
        # Assignment 1 is a medium assignment
        self.assertEqual(
            weekly_assignments.assignment_1.classification,
            BoatAssignment.Classification.MEDIUM,
        )
        self.assertIn(weekly_assignments.assignment_1, medium_assignments)
        # Assignment 2 is a track assignment
        self.assertEqual(
            weekly_assignments.assignment_2.classification,
            next_rank_track,
        )
        self.assertIn(
            weekly_assignments.assignment_2,
            assignments_by_track[next_rank_track],
        )

        # Rank 7 generates 1 medium and 2 from the chosen track
        for starting_rank in list(ranks_by_tier_and_track[7].values()):
            deckhand.rank = starting_rank
            deckhand.save()
            weekly_assignments = generate_weekly_assignments(
                deckhand, datetime.date(2025, 1, 1), self.user
            )
            # Correct assignments are generated
            self.assertIsNotNone(weekly_assignments.assignment_1)
            self.assertIsNotNone(weekly_assignments.assignment_2)
            self.assertIsNotNone(weekly_assignments.assignment_3)
            # Next rank is tier 8
            self.assertEqual(weekly_assignments.next_rank.tier, 8)
            next_rank_track = weekly_assignments.next_rank.track
            self.assertEqual(
                weekly_assignments.next_rank,
                ranks_by_tier_and_track[8][next_rank_track],
            )
            # Assignment 1 is a medium assignment
            self.assertEqual(
                weekly_assignments.assignment_1.classification,
                BoatAssignment.Classification.MEDIUM,
            )
            self.assertIn(weekly_assignments.assignment_1, medium_assignments)
            # Assignment 2 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_2.classification,
                next_rank_track,
            )
            self.assertIn(
                weekly_assignments.assignment_2,
                assignments_by_track[deckhand.rank.track],
            )
            # Assignment 3 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_3.classification,
                next_rank_track,
            )
            self.assertIn(
                weekly_assignments.assignment_3,
                assignments_by_track[deckhand.rank.track],
            )
            # Assignment 2 and 3 are different
            self.assertNotEqual(
                weekly_assignments.assignment_2, weekly_assignments.assignment_3
            )

        # Rank 8 generates 1 hard and 2 from the chosen track
        for starting_rank in list(ranks_by_tier_and_track[8].values()):
            deckhand.rank = starting_rank
            deckhand.save()
            weekly_assignments = generate_weekly_assignments(
                deckhand, datetime.date(2025, 1, 1), self.user
            )
            # Correct assignments are generated
            self.assertIsNotNone(weekly_assignments.assignment_1)
            self.assertIsNotNone(weekly_assignments.assignment_2)
            self.assertIsNotNone(weekly_assignments.assignment_3)
            # Next rank is tier 9
            self.assertEqual(weekly_assignments.next_rank.tier, 9)
            next_rank_track = weekly_assignments.next_rank.track
            self.assertEqual(
                weekly_assignments.next_rank,
                ranks_by_tier_and_track[9][next_rank_track],
            )
            # Assignment 1 is a hard assignment
            self.assertEqual(
                weekly_assignments.assignment_1.classification,
                BoatAssignment.Classification.HARD,
            )
            self.assertIn(weekly_assignments.assignment_1, hard_assignments)
            # Assignment 2 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_2.classification,
                next_rank_track,
            )
            self.assertIn(
                weekly_assignments.assignment_2,
                assignments_by_track[deckhand.rank.track],
            )
            # Assignment 3 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_3.classification,
                next_rank_track,
            )
            self.assertIn(
                weekly_assignments.assignment_3,
                assignments_by_track[deckhand.rank.track],
            )
            # Assignment 2 and 3 are different
            self.assertNotEqual(
                weekly_assignments.assignment_2, weekly_assignments.assignment_3
            )

        # Rank 9 generates 3 from the non-chosen track
        for starting_rank in list(ranks_by_tier_and_track[9].values()):
            deckhand.rank = random.choice(list(ranks_by_tier_and_track[9].values()))
            deckhand.save()
            expected_tracks = [
                BoatAssignment.Classification.COMMAND,
                BoatAssignment.Classification.CULINARY,
                BoatAssignment.Classification.HOSPITALITY,
                BoatAssignment.Classification.MACHINERY,
            ]
            expected_tracks.remove(deckhand.rank.track)
            weekly_assignments = generate_weekly_assignments(
                deckhand, datetime.date(2025, 1, 1), self.user
            )
            # Correct assignments are generated
            self.assertIsNotNone(weekly_assignments.assignment_1)
            self.assertIsNotNone(weekly_assignments.assignment_2)
            self.assertIsNotNone(weekly_assignments.assignment_3)
            # Next rank is tier 10
            self.assertEqual(weekly_assignments.next_rank.tier, 10)
            self.assertEqual(weekly_assignments.next_rank, tier10)
            # Assignment 1 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_1.classification,
                expected_tracks[0],
            )
            self.assertIn(
                weekly_assignments.assignment_1,
                assignments_by_track[expected_tracks[0]],
            )
            # Assignment 2 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_2.classification,
                expected_tracks[1],
            )
            self.assertIn(
                weekly_assignments.assignment_2,
                assignments_by_track[expected_tracks[1]],
            )
            # Assignment 3 is a track assignment
            self.assertEqual(
                weekly_assignments.assignment_3.classification,
                expected_tracks[2],
            )
            self.assertIn(
                weekly_assignments.assignment_3,
                assignments_by_track[expected_tracks[2]],
            )

        # Starting from Tier 10, weekly assignments do not generate
        deckhand.rank = tier10
        deckhand.save()
        with self.assertRaises(Exception):
            generate_weekly_assignments(deckhand, datetime.date(2025, 1, 1), self.user)

    @patch("apps.era_03.utils.match_stats")
    @patch("apps.era_03.utils.requests.Session")
    def test_save_new_matches(self, mock_Session, mock_match_stats):
        mock_match_stats.side_effect = [
            {
                "MatchId": "00000000-0000-0000-0000-000000000000",
                "MatchInfo": {
                    "StartTime": "2024-01-09T00:00:00.00Z",
                    "EndTime": "2024-01-09T01:20:34.567Z",
                },
            },
            {
                "MatchId": "11111111-1111-1111-1111-111111111111",
                "MatchInfo": {
                    "StartTime": "2025-01-09T00:00:00.00Z",
                    "EndTime": "2025-01-09T01:20:34.567Z",
                },
            },
            {
                "MatchId": "22222222-2222-2222-2222-222222222222",
                "MatchInfo": {
                    "StartTime": "2026-01-09T00:00:00.00Z",
                    "EndTime": "2026-01-09T01:20:34.567Z",
                },
            },
        ]
        result = save_new_matches(
            {
                "00000000-0000-0000-0000-000000000000",
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
            },
            self.user,
        )
        self.assertTrue(result)
        called_0 = False
        called_1 = False
        called_2 = False
        for mock_call in mock_match_stats.mock_calls:
            if mock_call == call(
                "00000000-0000-0000-0000-000000000000",
                mock_Session.return_value.__enter__.return_value,
            ):
                called_0 = True
            if mock_call == call(
                "11111111-1111-1111-1111-111111111111",
                mock_Session.return_value.__enter__.return_value,
            ):
                called_1 = True
            if mock_call == call(
                "22222222-2222-2222-2222-222222222222",
                mock_Session.return_value.__enter__.return_value,
            ):
                called_2 = True
        self.assertTrue(called_0 and called_1 and called_2)
        self.assertEqual(HaloInfiniteMatch.objects.count(), 3)

    def test_check_deckhand_promotion(self):
        tiers = [
            BoatRank.objects.create(creator=self.user, rank="Test1", tier=1),
            BoatRank.objects.create(creator=self.user, rank="Test2", tier=2),
            BoatRank.objects.create(creator=self.user, rank="Test3", tier=3),
            BoatRank.objects.create(creator=self.user, rank="Test4", tier=4),
            BoatRank.objects.create(creator=self.user, rank="Test5", tier=5),
            BoatRank.objects.create(creator=self.user, rank="Test6", tier=6),
            BoatRank.objects.create(creator=self.user, rank="Test7", tier=7),
            BoatRank.objects.create(creator=self.user, rank="Test8", tier=8),
            BoatRank.objects.create(creator=self.user, rank="Test9", tier=9),
            BoatRank.objects.create(creator=self.user, rank="Test10", tier=10),
        ]

        deckhand = BoatDeckhand.objects.create(
            creator=self.user,
            deckhand_id=self.discord_account.discord_id,
            rank=tiers[0],
        )

        # Ranks match
        self.assertFalse(
            check_deckhand_promotion(
                deckhand,
                WeeklyBoatAssignments(
                    creator=self.user,
                    deckhand=deckhand,
                    week_start=datetime.date(2025, 1, 1),
                    next_rank=tiers[0],
                ),
            )
        )

        # Ranks do not match (below rank 10)
        self.assertTrue(
            check_deckhand_promotion(
                deckhand,
                WeeklyBoatAssignments(
                    creator=self.user,
                    deckhand=deckhand,
                    week_start=datetime.date(2025, 1, 1),
                    next_rank=tiers[1],
                ),
            )
        )
        self.assertEqual(deckhand.rank, tiers[1])

        deckhand.rank = tiers[8]
        deckhand.save()

        # Promotion to rank 10 disallowed (not all secrets unlocked)
        self.assertFalse(
            check_deckhand_promotion(
                deckhand,
                WeeklyBoatAssignments(
                    creator=self.user,
                    deckhand=deckhand,
                    week_start=datetime.date(2025, 1, 1),
                    next_rank=tiers[9],
                ),
            )
        )

        for i in range(0, 7):
            secret = BoatSecret.objects.create(
                creator=self.user,
                title=f"TestSecret{i}",
                hint=f"TestHint{i}",
                medal_id=i,
            )
            with patch("apps.halo_infinite.signals.match_stats") as mock_match_stats:
                match_uuid = str(uuid.uuid4())
                mock_match_stats.return_value = {
                    "MatchId": match_uuid,
                    "MatchInfo": {
                        "StartTime": "2025-01-09T00:00:00.00Z",
                        "EndTime": "2025-01-09T01:20:34.567Z",
                    },
                }
                match = HaloInfiniteMatch.objects.create(
                    creator=self.user,
                    match_id=match_uuid,
                    start_time=datetime.datetime(2025, 1, 1),
                    end_time=datetime.datetime(2025, 1, 1),
                )
            BoatSecretUnlock.objects.create(
                creator=self.user, secret=secret, deckhand=deckhand, match=match
            )

        # Promotion to rank 10 allowed (all secrets unlocked)
        self.assertTrue(
            check_deckhand_promotion(
                deckhand,
                WeeklyBoatAssignments(
                    creator=self.user,
                    deckhand=deckhand,
                    week_start=datetime.date(2025, 1, 1),
                    next_rank=tiers[9],
                ),
            )
        )
        self.assertEqual(deckhand.rank, tiers[9])
