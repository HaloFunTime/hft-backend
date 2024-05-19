import datetime
from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.era_02.models import MVT
from apps.era_02.utils import fetch_match_ids_for_xuid, save_new_matches
from apps.halo_infinite.constants import ERA_2_END_TIME, ERA_2_START_TIME
from apps.halo_infinite.models import HaloInfiniteMatch


class Era01TestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_mvt_save(self):
        # Creating an MVT record should be successful
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="test", discord_username="ABC1234"
        )
        mvt = MVT.objects.create(
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(mvt.creator, self.user)
        self.assertEqual(mvt.earner_id, discord_account.discord_id)
        self.assertEqual(
            mvt.earned_at,
            datetime.datetime(2023, 10, 31, 0, 0, 0, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(discord_account.mvt, mvt)

        # Duplicate MVT record (same `earner`) should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "MVT_earner_id_key"\n'
            + "DETAIL:  Key (earner_id)=(test) already exists.\n",
            MVT.objects.create,
            creator=self.user,
            earner=discord_account,
            earned_at=datetime.datetime(
                2023, 7, 7, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )


class UtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.era_02.utils.matches_between")
    def test_fetch_match_ids_for_xuid(self, mock_matches_between):
        # With no data
        mock_matches_between.return_value = []
        match_ids = fetch_match_ids_for_xuid(123)
        mock_matches_between.assert_called_once_with(
            123,
            ERA_2_START_TIME,
            ERA_2_END_TIME,
            type="Matchmaking",
            session=None,
            ids_only=True,
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
            456,
            ERA_2_START_TIME,
            ERA_2_END_TIME,
            type="Matchmaking",
            session=None,
            ids_only=True,
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

    @patch("apps.era_02.utils.match_stats")
    @patch("apps.era_02.utils.requests.Session")
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
