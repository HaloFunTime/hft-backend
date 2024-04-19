import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.halo_infinite.models import HaloInfinitePlaylist
from apps.link.models import DiscordXboxLiveLink
from apps.link.utils import (
    auto_verify_discord_xbox_live_link,
    update_or_create_discord_xbox_live_link,
)
from apps.link.views import (
    LINK_ERROR_INVALID_DISCORD_ID,
    LINK_ERROR_INVALID_DISCORD_USERNAME,
    LINK_ERROR_MISSING_DISCORD_ID,
    LINK_ERROR_MISSING_DISCORD_USERNAME,
)
from apps.xbox_live.models import XboxLiveAccount


class LinkTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_discord_to_xbox_live_get(self, mock_get_xuid_and_exact_gamertag):
        # Missing `discordId` throws error
        response = self.client.get("/link/discord-to-xbox-live")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": LINK_ERROR_MISSING_DISCORD_ID})

        # Non-numeric `discordId` throws error
        response = self.client.get("/link/discord-to-xbox-live?discordId=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": LINK_ERROR_INVALID_DISCORD_ID})

        # Missing `discordUsername` throws error
        response = self.client.get("/link/discord-to-xbox-live?discordId=123")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": LINK_ERROR_MISSING_DISCORD_USERNAME})

        # Invalid `discordUsername` throws error
        response = self.client.get(
            "/link/discord-to-xbox-live?discordId=123&discordUsername=i"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"error": LINK_ERROR_INVALID_DISCORD_USERNAME})

        # No DiscordXboxLiveLink returns 404
        response = self.client.get(
            "/link/discord-to-xbox-live?discordId=123456789&discordUsername=Test0123"
        )
        self.assertEqual(response.status_code, 404)

        # Existing DiscordXboxLiveLink returns 200
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_username="ABC1234"
        )
        mock_get_xuid_and_exact_gamertag.return_value = (0, "Test123")
        xbox_live_account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="test123"
        )
        DiscordXboxLiveLink.objects.create(
            discord_account=discord_account,
            xbox_live_account=xbox_live_account,
            creator=self.user,
        )
        response = self.client.get(
            f"/link/discord-to-xbox-live?discordId={discord_account.discord_id}"
            f"&discordUsername={discord_account.discord_username}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), discord_account.discord_id)
        self.assertEqual(
            response.data.get("discordUsername"), discord_account.discord_username
        )
        self.assertEqual(response.data.get("xboxLiveXuid"), xbox_live_account.xuid)
        self.assertEqual(
            response.data.get("xboxLiveGamertag"), xbox_live_account.gamertag
        )
        self.assertEqual(response.data.get("verified"), False)

    @patch("apps.link.views.auto_verify_discord_xbox_live_link")
    @patch("apps.xbox_live.utils.get_xuid_and_exact_gamertag")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_discord_to_xbox_live_post(
        self,
        mock_signals_get_xuid_and_exact_gamertag,
        mock_utils_get_xuid_and_exact_gamertag,
        mock_auto_verify_discord_xbox_live_link,
    ):
        # For clarity, the auto-verify function is mocked to return the link unchanged
        mock_auto_verify_discord_xbox_live_link.side_effect = lambda x, _: x

        # Missing field values throw errors
        response = self.client.post("/link/discord-to-xbox-live", {}, format="json")
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
        self.assertIn("xboxLiveGamertag", details)
        self.assertEqual(
            details.get("xboxLiveGamertag"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {"discordUserId": "ABC", "discordUsername": "1", "xboxLiveGamertag": "2ed"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId"),
            [
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                )
            ],
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername"),
            [
                ErrorDetail(
                    string="Ensure this field has at least 2 characters.",
                    code="min_length",
                )
            ],
        )
        self.assertIn("xboxLiveGamertag", details)
        self.assertEqual(
            details.get("xboxLiveGamertag"),
            [
                ErrorDetail(
                    string="Only characters constituting a valid Xbox Live Gamertag are allowed.",
                    code="invalid",
                )
            ],
        )

        # Happy path - new record created (defaults to unverified)
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "test")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "test")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "123",
                "discordUsername": "Test0123",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUsername"), "Test0123")
        self.assertEqual(response.data.get("xboxLiveXuid"), 0)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "test")
        self.assertEqual(response.data.get("verified"), False)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(XboxLiveAccount.objects.count(), 1)
        mock_auto_verify_discord_xbox_live_link.assert_called_once_with(
            DiscordXboxLiveLink.objects.first(), self.user
        )
        mock_auto_verify_discord_xbox_live_link.reset_mock()
        # Approve the link record
        link = DiscordXboxLiveLink.objects.all().first()
        link.verifier = self.user
        link.verified = True
        link.save()

        # Repeat call with same Discord/Xbox IDs shouldn't change the link record's verification status
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "TEST")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "TEST")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "123",
                "discordUsername": "TEST0123",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUsername"), "TEST0123")
        self.assertEqual(response.data.get("xboxLiveXuid"), 0)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "TEST")
        self.assertEqual(response.data.get("verified"), True)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(XboxLiveAccount.objects.count(), 1)
        link = DiscordXboxLiveLink.objects.all().first()
        self.assertEqual(link.discord_account.discord_id, "123")
        self.assertEqual(link.xbox_live_account.xuid, 0)
        self.assertEqual(link.verified, True)
        self.assertEqual(link.verifier, self.user)
        mock_auto_verify_discord_xbox_live_link.assert_not_called()
        mock_auto_verify_discord_xbox_live_link.reset_mock()

        # If another Discord Account attempts to claim an already-linked Xbox Live Account, an error should be thrown
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "test")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "test")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "456",
                "discordUsername": "Test0456",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        self.assertEqual(XboxLiveAccount.objects.count(), 1)

        # If the original Discord Account attempts to link to a different Xbox Live Account, no error should be thrown
        # but the link record should now be unverified
        mock_signals_get_xuid_and_exact_gamertag.return_value = (1, "test1")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (1, "test1")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "123",
                "discordUsername": "Test0123",
                "xboxLiveGamertag": "Test1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUsername"), "Test0123")
        self.assertEqual(response.data.get("xboxLiveXuid"), 1)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "test1")
        self.assertEqual(response.data.get("verified"), False)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        self.assertEqual(XboxLiveAccount.objects.count(), 2)
        link = DiscordXboxLiveLink.objects.all().first()
        self.assertEqual(link.discord_account.discord_id, "123")
        self.assertEqual(link.xbox_live_account.xuid, 1)
        self.assertEqual(link.verified, False)
        self.assertEqual(link.verifier, None)
        mock_auto_verify_discord_xbox_live_link.assert_called_once_with(link, self.user)
        mock_auto_verify_discord_xbox_live_link.reset_mock()

        # Now the "other" Discord Account can link to the first Xbox Live Account without issue
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "test")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "test")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "456",
                "discordUsername": "Test0456",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "456")
        self.assertEqual(response.data.get("discordUsername"), "Test0456")
        self.assertEqual(response.data.get("xboxLiveXuid"), 0)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "test")
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        self.assertEqual(XboxLiveAccount.objects.count(), 2)
        mock_auto_verify_discord_xbox_live_link.assert_called_once_with(
            DiscordXboxLiveLink.objects.filter(xbox_live_account_id=0)[0], self.user
        )
        mock_auto_verify_discord_xbox_live_link.reset_mock()


class LinkUtilsTestCase(TestCase):
    @patch("apps.halo_infinite.signals.get_playlist_latest_version_info")
    @patch("apps.xbox_live.utils.get_xuid_and_exact_gamertag")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def setUp(
        self,
        mock_signals_get_xuid_and_exact_gamertag,
        mock_utils_get_xuid_and_exact_gamertag,
        mock_get_playlist_latest_version_info,
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
        mock_get_playlist_latest_version_info.return_value = {
            "playlist_id": test_playlist_id,
            "version_id": uuid.uuid4(),
            "ranked": True,
            "name": "name",
            "description": "description",
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
