import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.discord.models import DiscordAccount
from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.link.models import DiscordXboxLiveLink
from apps.link.utils import (
    auto_verify_discord_xbox_live_link,
    update_or_create_discord_xbox_live_link,
)
from apps.xbox_live.models import XboxLiveAccount


class LinkUtilsTestCase(TestCase):
    @patch("apps.halo_infinite.signals.get_playlist")
    @patch("apps.halo_infinite.signals.get_playlist_info")
    @patch("apps.xbox_live.utils.get_xuid_and_exact_gamertag")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def setUp(
        self,
        mock_signals_get_xuid_and_exact_gamertag,
        mock_utils_get_xuid_and_exact_gamertag,
        mock_get_playlist_info,
        mock_get_playlist,
    ):
        def set_both_mock_return_values(return_value):
            mock_signals_get_xuid_and_exact_gamertag.return_value = return_value
            mock_utils_get_xuid_and_exact_gamertag.return_value = return_value

        def reset_both_mocks():
            mock_signals_get_xuid_and_exact_gamertag.reset_mock()
            mock_utils_get_xuid_and_exact_gamertag.reset_mock()

        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        self.discord_account_1 = DiscordAccount.objects.create(
            creator=self.user, discord_id="1", discord_username="Username1"
        )
        self.discord_account_2 = DiscordAccount.objects.create(
            creator=self.user, discord_id="2", discord_username="Username2"
        )

        set_both_mock_return_values((1, "xbl1"))
        self.xbox_live_account_1 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL1"
        )
        reset_both_mocks()
        set_both_mock_return_values((2, "xbl2"))
        self.xbox_live_account_2 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL2"
        )
        reset_both_mocks()
        set_both_mock_return_values((3, "xbl3"))
        self.xbox_live_account_3 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL3"
        )
        reset_both_mocks()

        test_playlist_id = uuid.uuid4()
        test_version_id = uuid.uuid4()
        mock_get_playlist_info.return_value = {
            "UgcPlaylistVersion": str(test_version_id),
            "HasCsr": True,
        }
        mock_get_playlist.return_value = {
            "AssetId": str(test_playlist_id),
            "VersionId": str(test_version_id),
            "PublicName": "name",
            "Description": "description",
        }
        self.playlist = HaloInfinitePlaylist.objects.create(
            creator=self.user, playlist_id=test_playlist_id, active=True
        )

    def test_update_or_create_discord_xbox_live_link(self):
        # Initial call creates DiscordXboxLiveLink
        discord_xbox_live_link_1 = update_or_create_discord_xbox_live_link(
            self.discord_account_1, self.xbox_live_account_1, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_1.discord_account, self.discord_account_1
        )
        self.assertEqual(
            discord_xbox_live_link_1.xbox_live_account, self.xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_1.verified, False)
        self.assertIsNone(discord_xbox_live_link_1.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)

        # Call with same DiscordAccount and different XboxLiveAccount should update the existing link record
        discord_xbox_live_link_2 = update_or_create_discord_xbox_live_link(
            self.discord_account_1, self.xbox_live_account_2, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_2.discord_account, self.discord_account_1
        )
        self.assertEqual(
            discord_xbox_live_link_2.xbox_live_account, self.xbox_live_account_2
        )
        self.assertEqual(discord_xbox_live_link_2.verified, False)
        self.assertIsNone(discord_xbox_live_link_2.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)

        # Call with different DiscordAccount trying to link to the already-linked XboxLiveAccount should raise
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "DiscordXboxLiveLink_xbox_live_account_id_key"',
            lambda: update_or_create_discord_xbox_live_link(
                self.discord_account_2, self.xbox_live_account_2, self.user
            ),
        )

        # Call with orphaned records should allow creation of new DiscordXboxLiveLink
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            self.discord_account_2, self.xbox_live_account_1, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_3.discord_account, self.discord_account_2
        )
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, self.xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with same arguments should preserve existing verification status (False)
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            self.discord_account_2, self.xbox_live_account_1, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_3.discord_account, self.discord_account_2
        )
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, self.xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with same arguments should preserve existing verification status (True)
        discord_xbox_live_link_3.verified = True
        discord_xbox_live_link_3.verifier = self.user
        discord_xbox_live_link_3.save()
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            self.discord_account_2, self.xbox_live_account_1, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_3.discord_account, self.discord_account_2
        )
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, self.xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, True)
        self.assertEqual(discord_xbox_live_link_3.verifier, self.user)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with a new XboxLiveAccount should reset verified to False and clear verifier
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            self.discord_account_2, self.xbox_live_account_3, self.user
        )
        self.assertEqual(
            discord_xbox_live_link_3.discord_account, self.discord_account_2
        )
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, self.xbox_live_account_3
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

    @patch("apps.link.utils.get_contributor_xuids_for_maps_in_active_playlists")
    @patch("apps.link.utils.get_csrs")
    @patch("apps.link.utils.get_career_ranks")
    def test_auto_verify_discord_xbox_live_link(
        self,
        mock_get_career_ranks,
        mock_get_csrs,
        mock_get_contributor_xuids_for_maps_in_active_playlists,
    ):
        link_1 = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account_id=self.discord_account_1.discord_id,
            xbox_live_account_id=self.xbox_live_account_1.xuid,
        )
        link_2 = DiscordXboxLiveLink.objects.create(
            creator=self.user,
            discord_account_id=self.discord_account_2.discord_id,
            xbox_live_account_id=self.xbox_live_account_2.xuid,
        )
        # NO CHANGE: null return data
        mock_get_career_ranks.return_value = {}
        mock_get_csrs.return_value = {}
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = set()
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # NO CHANGE: zero Career Rank, no CSR, no matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 0}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": -1}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = set()
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # NO CHANGE: non-zero Career Rank, Onyx CSR, no matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": 1500}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = set()
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # NO CHANGE: non-zero Career Rank, no CSR, matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": -1}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = {
            self.xbox_live_account_1.xuid
        }
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # NO CHANGE: non-zero Career Rank, non-Onyx CSR, matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": 1499}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = {
            self.xbox_live_account_1.xuid
        }
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # NO CHANGE: non-zero Career Rank, Onyx CSR, matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": 1500}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = {
            self.xbox_live_account_1.xuid
        }
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertFalse(updated_link.verified)
        self.assertIsNone(updated_link.verifier)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # AUTO VERIFICATION: non-zero Career Rank, no CSR, no matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_1.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_1.xuid: {"all_time_max_csr": -1}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = set()
        updated_link = auto_verify_discord_xbox_live_link(link_1, self.user)
        self.assertTrue(updated_link.verified)
        self.assertEqual(updated_link.verifier, self.user)
        mock_get_career_ranks.assert_called_once_with([link_1.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_1.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()

        # AUTO VERIFICATION: non-zero Career Rank, non-Onyx CSR, no matchmaking map credit
        mock_get_career_ranks.return_value = {
            "career_ranks": {self.xbox_live_account_2.xuid: {"cumulative_score": 1}}
        }
        mock_get_csrs.return_value = {
            "csrs": {self.xbox_live_account_2.xuid: {"all_time_max_csr": 1499}}
        }
        mock_get_contributor_xuids_for_maps_in_active_playlists.return_value = set()
        updated_link = auto_verify_discord_xbox_live_link(link_2, self.user)
        self.assertTrue(updated_link.verified)
        self.assertEqual(updated_link.verifier, self.user)
        mock_get_career_ranks.assert_called_once_with([link_2.xbox_live_account_id])
        mock_get_csrs.assert_called_once_with(
            [link_2.xbox_live_account_id], self.playlist.playlist_id
        )
        mock_get_contributor_xuids_for_maps_in_active_playlists.assert_called_once()
        mock_get_career_ranks.reset_mock()
        mock_get_csrs.reset_mock()
        mock_get_contributor_xuids_for_maps_in_active_playlists.reset_mock()
