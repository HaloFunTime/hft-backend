import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.halo_infinite.views import (
    ERROR_GAMERTAG_INVALID,
    ERROR_GAMERTAG_MISSING,
    ERROR_GAMERTAG_NOT_FOUND,
)


class HaloInfiniteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.halo_infinite.views.get_csrs")
    @patch("apps.halo_infinite.signals.get_playlist_latest_version_info")
    @patch("apps.halo_infinite.views.get_xuid_and_exact_gamertag")
    def test_csr_view(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_get_playlist_latest_version_info,
        mock_get_csrs,
    ):
        # Missing `gamertag` throws error
        response = self.client.get("/halo-infinite/csr")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_MISSING, code="parse_error"),
        )

        # Invalid `gamertag` throws error
        response = self.client.get("/halo-infinite/csr?gamertag=2fast")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_INVALID, code="parse_error"),
        )

        # Inability to retrieve gamertag/xuid throws error
        mock_get_xuid_and_exact_gamertag.return_value = (None, None)
        response = self.client.get("/halo-infinite/csr?gamertag=Intern")
        self.assertEqual(response.status_code, 404)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_NOT_FOUND, code="not_found"),
        )
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_xuid_and_exact_gamertag.reset_mock()

        # No active ranked playlists in DB results in mostly empty payload
        mock_get_xuid_and_exact_gamertag.return_value = (0, "InternActualGT")
        response = self.client.get("/halo-infinite/csr?gamertag=Intern")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("gamertag"), "InternActualGT")
        self.assertEqual(response.data.get("xuid"), "0")
        self.assertEqual(response.data.get("playlists"), [])
        mock_get_xuid_and_exact_gamertag.reset_mock()

        # Add an active ranked playlist to the DB
        ranked_test_playlist_id_1 = uuid.uuid4()
        ranked_test_version_id_1 = uuid.uuid4()
        mock_get_playlist_latest_version_info.return_value = {
            "playlist_id": ranked_test_playlist_id_1,
            "version_id": ranked_test_version_id_1,
            "ranked": True,
            "name": "name",
            "description": "description",
        }
        ranked_test_playlist_1 = HaloInfinitePlaylist.objects.create(
            creator=self.user, playlist_id=ranked_test_playlist_id_1, active=True
        )

        # Exception in get_csrs throws error
        mock_get_xuid_and_exact_gamertag.return_value = (0, "InternActualGT")
        mock_get_csrs.side_effect = Exception()
        response = self.client.get("/halo-infinite/csr?gamertag=Intern")
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Could not get CSR for gamertag InternActualGT.", code="error"
            ),
        )
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_csrs.assert_called_once_with([0], ranked_test_playlist_id_1)
        mock_get_xuid_and_exact_gamertag.reset_mock()
        mock_get_csrs.reset_mock()

        # Success returns 200
        mock_get_xuid_and_exact_gamertag.return_value = (0, "InternActualGT")
        mock_get_csrs.return_value = {
            "csrs": {
                0: {
                    "current_csr": 1000,
                    "current_tier": "Platinum",
                    "current_subtier": 2,
                    "current_reset_max_csr": 1200,
                    "current_reset_max_tier": "Diamond",
                    "current_reset_max_subtier": 0,
                    "all_time_max_csr": 1500,
                    "all_time_max_tier": "Onyx",
                    "all_time_max_subtier": 0,
                }
            }
        }
        mock_get_csrs.side_effect = None
        response = self.client.get("/halo-infinite/csr?gamertag=Intern")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("gamertag"), "InternActualGT")
        self.assertEqual(response.data.get("xuid"), "0")
        playlists = response.data.get("playlists")
        self.assertIsNotNone(playlists)
        for playlist in playlists:
            self.assertEqual(
                playlist.get("playlist_id"), str(ranked_test_playlist_1.playlist_id)
            )
            self.assertEqual(
                playlist.get("playlist_name"), str(ranked_test_playlist_1.name)
            )
            self.assertEqual(
                playlist.get("playlist_description"),
                str(ranked_test_playlist_1.description),
            )
            current = playlist.get("current")
            self.assertIsNotNone(current)
            self.assertEqual(current.get("csr"), 1000)
            self.assertEqual(current.get("tier"), "Platinum")
            self.assertEqual(current.get("subtier"), 2)
            current_reset_max = playlist.get("current_reset_max")
            self.assertIsNotNone(current_reset_max)
            self.assertEqual(current_reset_max.get("csr"), 1200)
            self.assertEqual(current_reset_max.get("tier"), "Diamond")
            self.assertEqual(current_reset_max.get("subtier"), 0)
            all_time_max = playlist.get("all_time_max")
            self.assertIsNotNone(all_time_max)
            self.assertEqual(all_time_max.get("csr"), 1500)
            self.assertEqual(all_time_max.get("tier"), "Onyx")
            self.assertEqual(all_time_max.get("subtier"), 0)
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_csrs.assert_called_once_with([0], ranked_test_playlist_id_1)
        mock_get_xuid_and_exact_gamertag.reset_mock()
        mock_get_csrs.reset_mock()

    @patch("apps.halo_infinite.views.get_summary_stats")
    @patch("apps.halo_infinite.views.get_xuid_and_exact_gamertag")
    def test_summary_stats_view(
        self, mock_get_xuid_and_exact_gamertag, mock_get_summary_stats
    ):
        # Missing `gamertag` throws error
        response = self.client.get("/halo-infinite/summary-stats")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_MISSING, code="parse_error"),
        )

        # Invalid `gamertag` throws error
        response = self.client.get("/halo-infinite/summary-stats?gamertag=2fast")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_INVALID, code="parse_error"),
        )

        # Inability to retrieve gamertag/xuid throws error
        mock_get_xuid_and_exact_gamertag.return_value = (None, None)
        response = self.client.get("/halo-infinite/summary-stats?gamertag=Intern")
        self.assertEqual(response.status_code, 404)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(string=ERROR_GAMERTAG_NOT_FOUND, code="not_found"),
        )
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_xuid_and_exact_gamertag.reset_mock()

        # Exception in get_summary_stats throws error
        mock_get_xuid_and_exact_gamertag.return_value = (0, "InternActualGT")
        mock_get_summary_stats.side_effect = Exception()
        response = self.client.get("/halo-infinite/summary-stats?gamertag=Intern")
        self.assertEqual(response.status_code, 500)
        details = response.data.get("error").get("details")
        self.assertEqual(
            details.get("detail"),
            ErrorDetail(
                string="Could not get summary stats for gamertag InternActualGT.",
                code="error",
            ),
        )
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_summary_stats.assert_called_once_with(0)
        mock_get_xuid_and_exact_gamertag.reset_mock()
        mock_get_summary_stats.reset_mock()

        # Success returns 200
        mock_get_xuid_and_exact_gamertag.return_value = (0, "InternActualGT")
        mock_get_summary_stats.return_value = {
            "matchmaking": {
                "games_played": 10,
                "wins": 1,
                "losses": 2,
                "ties": 3,
                "kills": 4,
                "deaths": 5,
                "assists": 6,
                "kda": 7.89,
            },
            "custom": {
                "games_played": 11,
            },
            "local": {
                "games_played": 12,
            },
            "games_played": 33,
        }
        mock_get_summary_stats.side_effect = None
        response = self.client.get("/halo-infinite/summary-stats?gamertag=Intern")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("gamertag"), "InternActualGT")
        self.assertEqual(response.data.get("xuid"), "0")
        self.assertEqual(response.data.get("games_played"), 33)
        matchmaking = response.data.get("matchmaking")
        self.assertIsNotNone(matchmaking)
        self.assertEqual(matchmaking.get("games_played"), 10)
        self.assertEqual(matchmaking.get("wins"), 1)
        self.assertEqual(matchmaking.get("losses"), 2)
        self.assertEqual(matchmaking.get("ties"), 3)
        self.assertEqual(matchmaking.get("kills"), 4)
        self.assertEqual(matchmaking.get("deaths"), 5)
        self.assertEqual(matchmaking.get("assists"), 6)
        self.assertEqual(matchmaking.get("kda"), 7.89)
        custom = response.data.get("custom")
        self.assertIsNotNone(custom)
        self.assertEqual(custom.get("games_played"), 11)
        local = response.data.get("local")
        self.assertIsNotNone(local)
        self.assertEqual(local.get("games_played"), 12)
        mock_get_xuid_and_exact_gamertag.assert_called_once_with("Intern")
        mock_get_summary_stats.assert_called_once_with(0)
        mock_get_xuid_and_exact_gamertag.reset_mock()
        mock_get_summary_stats.reset_mock()
