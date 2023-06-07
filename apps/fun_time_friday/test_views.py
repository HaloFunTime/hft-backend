import datetime

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.discord.models import DiscordAccount
from apps.fun_time_friday.models import (
    FunTimeFridayVoiceConnect,
    FunTimeFridayVoiceDisconnect,
)


class FunTimeFridayTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_voice_connect_post(self):
        # Missing field values throw errors
        response = self.client.post("/fun-time-friday/voice-connect", {}, format="json")
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "connectorDiscordId",
            "connectorDiscordUsername",
            "connectedAt",
            "channelId",
        ]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/fun-time-friday/voice-connect",
            {
                "connectorDiscordId": "abc",
                "connectorDiscordUsername": "a",
                "connectedAt": "abc",
                "channelId": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for id_field in ["connectorDiscordId", "channelId"]:
            self.assertIn(id_field, details)
            self.assertEqual(
                details.get(id_field)[0],
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                ),
            )
        self.assertIn("connectorDiscordUsername", details)
        self.assertEqual(
            details.get("connectorDiscordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("connectedAt", details)
        self.assertEqual(
            details.get("connectedAt")[0],
            ErrorDetail(
                string="Datetime has wrong format. Use one of these formats instead: "
                "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].",
                code="invalid",
            ),
        )

        # Success (excluding channel name)
        response = self.client.post(
            "/fun-time-friday/voice-connect",
            {
                "connectorDiscordId": "123",
                "connectorDiscordUsername": "Test0123",
                "connectedAt": "2023-03-10T09:08:07Z",
                "channelId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        voice_connect = FunTimeFridayVoiceConnect.objects.first()
        self.assertEqual(voice_connect.connector_discord.discord_id, "123")
        self.assertEqual(voice_connect.connector_discord.discord_username, "Test0123")
        self.assertEqual(
            voice_connect.connected_at,
            datetime.datetime(
                year=2023,
                month=3,
                day=10,
                hour=9,
                minute=8,
                second=7,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(voice_connect.channel_id, "456")
        self.assertEqual(voice_connect.channel_name, "")
        voice_connect.delete()

        # Success (including channel name)
        response = self.client.post(
            "/fun-time-friday/voice-connect",
            {
                "connectorDiscordId": "123",
                "connectorDiscordUsername": "Test0124",
                "connectedAt": "2023-03-11T00:01:02Z",
                "channelId": "789",
                "channelName": "This channel name is a bit longer than fifty characters",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0124")
        voice_connect = FunTimeFridayVoiceConnect.objects.first()
        self.assertEqual(voice_connect.connector_discord.discord_id, "123")
        self.assertEqual(voice_connect.connector_discord.discord_username, "Test0124")
        self.assertEqual(
            voice_connect.connected_at,
            datetime.datetime(
                year=2023,
                month=3,
                day=11,
                hour=0,
                minute=1,
                second=2,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(voice_connect.channel_id, "789")
        self.assertEqual(
            voice_connect.channel_name,
            "This channel name is a bit longer than fifty chara",
        )
        voice_connect.delete()

    def test_voice_disconnect_post(self):
        # Missing field values throw errors
        response = self.client.post(
            "/fun-time-friday/voice-disconnect", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for field in [
            "disconnectorDiscordId",
            "disconnectorDiscordUsername",
            "disconnectedAt",
            "channelId",
        ]:
            self.assertIn(field, details)
            self.assertEqual(
                details.get(field),
                [ErrorDetail(string="This field is required.", code="required")],
            )

        # Improperly formatted values throw errors
        response = self.client.post(
            "/fun-time-friday/voice-disconnect",
            {
                "disconnectorDiscordId": "abc",
                "disconnectorDiscordUsername": "a",
                "disconnectedAt": "abc",
                "channelId": "abc",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        for id_field in ["disconnectorDiscordId", "channelId"]:
            self.assertIn(id_field, details)
            self.assertEqual(
                details.get(id_field)[0],
                ErrorDetail(
                    string="Only numeric characters are allowed.", code="invalid"
                ),
            )
        self.assertIn("disconnectorDiscordUsername", details)
        self.assertEqual(
            details.get("disconnectorDiscordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )
        self.assertIn("disconnectedAt", details)
        self.assertEqual(
            details.get("disconnectedAt")[0],
            ErrorDetail(
                string="Datetime has wrong format. Use one of these formats instead: "
                "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].",
                code="invalid",
            ),
        )

        # Success (excluding channel name)
        response = self.client.post(
            "/fun-time-friday/voice-disconnect",
            {
                "disconnectorDiscordId": "123",
                "disconnectorDiscordUsername": "Test0123",
                "disconnectedAt": "2023-03-10T09:08:07Z",
                "channelId": "456",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0123")
        voice_disconnect = FunTimeFridayVoiceDisconnect.objects.first()
        self.assertEqual(voice_disconnect.disconnector_discord.discord_id, "123")
        self.assertEqual(
            voice_disconnect.disconnector_discord.discord_username, "Test0123"
        )
        self.assertEqual(
            voice_disconnect.disconnected_at,
            datetime.datetime(
                year=2023,
                month=3,
                day=10,
                hour=9,
                minute=8,
                second=7,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(voice_disconnect.channel_id, "456")
        self.assertEqual(voice_disconnect.channel_name, "")
        voice_disconnect.delete()

        # Success (including channel name)
        response = self.client.post(
            "/fun-time-friday/voice-disconnect",
            {
                "disconnectorDiscordId": "123",
                "disconnectorDiscordUsername": "Test0124",
                "disconnectedAt": "2023-03-11T00:01:02Z",
                "channelId": "789",
                "channelName": "This channel name is a bit longer than fifty characters",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        discord_account = DiscordAccount.objects.first()
        self.assertEqual(discord_account.discord_id, "123")
        self.assertEqual(discord_account.discord_username, "Test0124")
        voice_disconnect = FunTimeFridayVoiceDisconnect.objects.first()
        self.assertEqual(voice_disconnect.disconnector_discord.discord_id, "123")
        self.assertEqual(
            voice_disconnect.disconnector_discord.discord_username, "Test0124"
        )
        self.assertEqual(
            voice_disconnect.disconnected_at,
            datetime.datetime(
                year=2023,
                month=3,
                day=11,
                hour=0,
                minute=1,
                second=2,
                tzinfo=datetime.timezone.utc,
            ),
        )
        self.assertEqual(voice_disconnect.channel_id, "789")
        self.assertEqual(
            voice_disconnect.channel_name,
            "This channel name is a bit longer than fifty chara",
        )
        voice_disconnect.delete()
