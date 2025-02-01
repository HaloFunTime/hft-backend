from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
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

    @patch("apps.link.views.get_gamertag_from_xuid")
    @patch("apps.xbox_live.signals.get_gamertag_from_xuid")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_discord_to_xbox_live_get(
        self,
        mock_get_xuid_and_exact_gamertag,
        mock_signals_get_gamertag_from_xuid,
        mock_views_get_gamertag_from_xuid,
    ):
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
        mock_views_get_gamertag_from_xuid.return_value = "Test321"
        mock_signals_get_gamertag_from_xuid.return_value = "Test321"
        response = self.client.get(
            f"/link/discord-to-xbox-live?discordId={discord_account.discord_id}"
            f"&discordUsername={discord_account.discord_username}"
        )
        mock_views_get_gamertag_from_xuid.assert_called_once_with(
            xbox_live_account.xuid
        )
        mock_signals_get_gamertag_from_xuid.assert_called_once_with(
            xbox_live_account.xuid
        )
        xbox_live_account.refresh_from_db()
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
    @patch("apps.xbox_live.signals.get_gamertag_from_xuid")
    def test_discord_to_xbox_live_post(
        self,
        mock_signals_get_gamertag_from_xuid,
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
        mock_signals_get_gamertag_from_xuid.return_value = "test"
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
        mock_signals_get_gamertag_from_xuid.return_value = "TEST"
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
        mock_signals_get_gamertag_from_xuid.return_value = "test"
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
        mock_signals_get_gamertag_from_xuid.return_value = "test1"
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
        mock_signals_get_gamertag_from_xuid.return_value = "test"
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
