from unittest.mock import patch

from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.link.models import DiscordXboxLiveLink
from apps.link.utils import update_or_create_discord_xbox_live_link
from apps.link.views import LINK_ERROR_INVALID_DISCORD_ID, LINK_ERROR_MISSING_DISCORD_ID
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

        # No DiscordXboxLiveLink returns 404
        response = self.client.get("/link/discord-to-xbox-live?discordId=123456789")
        self.assertEqual(response.status_code, 404)

        # Existing DiscordXboxLiveLink returns 200
        discord_account = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_tag="ABC#1234"
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
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), discord_account.discord_id)
        self.assertEqual(
            response.data.get("discordUserTag"), discord_account.discord_tag
        )
        self.assertEqual(response.data.get("xboxLiveXuid"), xbox_live_account.xuid)
        self.assertEqual(
            response.data.get("xboxLiveGamertag"), xbox_live_account.gamertag
        )
        self.assertEqual(response.data.get("verified"), False)

    @patch("apps.xbox_live.utils.get_xuid_and_exact_gamertag")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_discord_to_xbox_live_post(
        self,
        mock_signals_get_xuid_and_exact_gamertag,
        mock_utils_get_xuid_and_exact_gamertag,
    ):
        # Missing field values throw errors
        response = self.client.post("/link/discord-to-xbox-live", {}, format="json")
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
        self.assertIn("xboxLiveGamertag", details)
        self.assertEqual(
            details.get("xboxLiveGamertag"),
            [ErrorDetail(string="This field is required.", code="required")],
        )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {"discordUserId": "ABC", "discordUserTag": "1", "xboxLiveGamertag": "2ed"},
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
        self.assertIn("discordUserTag", details)
        self.assertEqual(
            details.get("discordUserTag"),
            [ErrorDetail(string="One '#' character is required.", code="invalid")],
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
                "discordUserTag": "Test#0123",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUserTag"), "Test#0123")
        self.assertEqual(response.data.get("xboxLiveXuid"), 0)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "test")
        self.assertEqual(response.data.get("verified"), False)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)
        self.assertEqual(DiscordAccount.objects.count(), 1)
        self.assertEqual(XboxLiveAccount.objects.count(), 1)
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
                "discordUserTag": "TEST#0123",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUserTag"), "TEST#0123")
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

        # If another Discord Account attempts to claim an already-linked Xbox Live Account, an error should be thrown
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "test")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "test")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "456",
                "discordUserTag": "Test#0456",
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
                "discordUserTag": "Test#0123",
                "xboxLiveGamertag": "Test1",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("discordUserTag"), "Test#0123")
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

        # Now the "other" Discord Account can link to the first Xbox Live Account without issue
        mock_signals_get_xuid_and_exact_gamertag.return_value = (0, "test")
        mock_utils_get_xuid_and_exact_gamertag.return_value = (0, "test")
        response = self.client.post(
            "/link/discord-to-xbox-live",
            {
                "discordUserId": "456",
                "discordUserTag": "Test#0456",
                "xboxLiveGamertag": "Test",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get("discordUserId"), "456")
        self.assertEqual(response.data.get("discordUserTag"), "Test#0456")
        self.assertEqual(response.data.get("xboxLiveXuid"), 0)
        self.assertEqual(response.data.get("xboxLiveGamertag"), "test")
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)
        self.assertEqual(DiscordAccount.objects.count(), 2)
        self.assertEqual(XboxLiveAccount.objects.count(), 2)


class LinkUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.xbox_live.utils.get_xuid_and_exact_gamertag")
    @patch("apps.xbox_live.signals.get_xuid_and_exact_gamertag")
    def test_update_or_create_discord_xbox_live_link(
        self,
        mock_signals_get_xuid_and_exact_gamertag,
        mock_utils_get_xuid_and_exact_gamertag,
    ):
        def set_both_mock_return_values(return_value):
            mock_signals_get_xuid_and_exact_gamertag.return_value = return_value
            mock_utils_get_xuid_and_exact_gamertag.return_value = return_value

        def reset_both_mocks():
            mock_signals_get_xuid_and_exact_gamertag.reset_mock()
            mock_utils_get_xuid_and_exact_gamertag.reset_mock()

        discord_account_1 = DiscordAccount.objects.create(
            creator=self.user, discord_id="123", discord_tag="ABC#1234"
        )
        discord_account_2 = DiscordAccount.objects.create(
            creator=self.user, discord_id="456", discord_tag="ABC#1234"
        )
        set_both_mock_return_values((1, "xbl1"))
        xbox_live_account_1 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL1"
        )
        reset_both_mocks()
        set_both_mock_return_values((2, "xbl2"))
        xbox_live_account_2 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL2"
        )
        reset_both_mocks()
        set_both_mock_return_values((3, "xbl3"))
        xbox_live_account_3 = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="XBL3"
        )
        reset_both_mocks()

        # Initial call creates DiscordXboxLiveLink
        discord_xbox_live_link_1 = update_or_create_discord_xbox_live_link(
            discord_account_1, xbox_live_account_1, self.user
        )
        self.assertEqual(discord_xbox_live_link_1.discord_account, discord_account_1)
        self.assertEqual(
            discord_xbox_live_link_1.xbox_live_account, xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_1.verified, False)
        self.assertIsNone(discord_xbox_live_link_1.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)

        # Call with same DiscordAccount and different XboxLiveAccount should update the existing link record
        discord_xbox_live_link_2 = update_or_create_discord_xbox_live_link(
            discord_account_1, xbox_live_account_2, self.user
        )
        self.assertEqual(discord_xbox_live_link_2.discord_account, discord_account_1)
        self.assertEqual(
            discord_xbox_live_link_2.xbox_live_account, xbox_live_account_2
        )
        self.assertEqual(discord_xbox_live_link_2.verified, False)
        self.assertIsNone(discord_xbox_live_link_2.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 1)

        # Call with different DiscordAccount trying to link to the already-linked XboxLiveAccount should raise
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "DiscordXboxLiveLink_xbox_live_account_id_key"',
            lambda: update_or_create_discord_xbox_live_link(
                discord_account_2, xbox_live_account_2, self.user
            ),
        )

        # Call with orphaned records should allow creation of new DiscordXboxLiveLink
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            discord_account_2, xbox_live_account_1, self.user
        )
        self.assertEqual(discord_xbox_live_link_3.discord_account, discord_account_2)
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with same arguments should preserve existing verification status (False)
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            discord_account_2, xbox_live_account_1, self.user
        )
        self.assertEqual(discord_xbox_live_link_3.discord_account, discord_account_2)
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with same arguments should preserve existing verification status (True)
        discord_xbox_live_link_3.verified = True
        discord_xbox_live_link_3.verifier = self.user
        discord_xbox_live_link_3.save()
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            discord_account_2, xbox_live_account_1, self.user
        )
        self.assertEqual(discord_xbox_live_link_3.discord_account, discord_account_2)
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, xbox_live_account_1
        )
        self.assertEqual(discord_xbox_live_link_3.verified, True)
        self.assertEqual(discord_xbox_live_link_3.verifier, self.user)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)

        # Update with a new XboxLiveAccount should reset verified to False and clear verifier
        discord_xbox_live_link_3 = update_or_create_discord_xbox_live_link(
            discord_account_2, xbox_live_account_3, self.user
        )
        self.assertEqual(discord_xbox_live_link_3.discord_account, discord_account_2)
        self.assertEqual(
            discord_xbox_live_link_3.xbox_live_account, xbox_live_account_3
        )
        self.assertEqual(discord_xbox_live_link_3.verified, False)
        self.assertIsNone(discord_xbox_live_link_3.verifier)
        self.assertEqual(DiscordXboxLiveLink.objects.count(), 2)
