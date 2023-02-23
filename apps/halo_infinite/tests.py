import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.halo_infinite.exceptions import (
    HaloInfiniteSpartanTokenMissingException,
    HaloInfiniteXSTSTokenMissingException,
)
from apps.halo_infinite.models import HaloInfiniteSpartanToken, HaloInfiniteXSTSToken
from apps.halo_infinite.tokens import (
    generate_spartan_token,
    generate_xsts_token,
    get_spartan_token,
    get_xsts_token,
)
from apps.xbox_live.models import XboxLiveUserToken


class HaloInfiniteTokensTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.halo_infinite.tokens.requests.Session")
    def test_generate_xsts_token(self, mock_Session):
        user_token = XboxLiveUserToken.objects.create(
            creator=self.user,
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )

        # Successful status code should create another HaloInfiniteXSTSToken record with unique properties
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.post.return_value.json.return_value = {
            "IssueInstant": "2023-02-14T06:22:23.3510901Z",
            "NotAfter": "2023-02-14T22:22:23.3510901Z",
            "Token": "xsts_test_token",
            "DisplayClaims": {
                "xui": [
                    {
                        "gtg": "HFT Intern",
                        "xid": "2535405290989773",
                        "uhs": "xsts_test_uhs",
                        "agg": "Adult",
                        "utr": "190",
                        "prv": "184 185 186 187 188 191 193 195 196 198 199 200 201 203 204 205 206 208 211 217 220 224 227 228 235 238 245 247 249 252 254 255",  # noqa: E501
                    }
                ]
            },
        }
        new_xsts_token = generate_xsts_token(user_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://xsts.auth.xboxlive.com/xsts/authorize",
            json={
                "Properties": {"SandboxId": "RETAIL", "UserTokens": [user_token.token]},
                "RelyingParty": "https://prod.xsts.halowaypoint.com/",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(HaloInfiniteXSTSToken.objects.all().count(), 1)
        self.assertIsNotNone(new_xsts_token.id)
        self.assertEqual(
            new_xsts_token.issue_instant,
            datetime.datetime(2023, 2, 14, 6, 22, 23, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            new_xsts_token.not_after,
            datetime.datetime(2023, 2, 14, 22, 22, 23, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(new_xsts_token.token, "xsts_test_token")
        self.assertEqual(new_xsts_token.uhs, "xsts_test_uhs")

        # Unsuccessful status code should return None and not create a new XboxLiveUserToken record
        mock_Session.reset_mock()
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            401
        )
        new_xsts_token = generate_xsts_token(user_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://xsts.auth.xboxlive.com/xsts/authorize",
            json={
                "Properties": {"SandboxId": "RETAIL", "UserTokens": [user_token.token]},
                "RelyingParty": "https://prod.xsts.halowaypoint.com/",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(HaloInfiniteXSTSToken.objects.all().count(), 1)
        self.assertIsNone(new_xsts_token)

    @patch("apps.halo_infinite.tokens.generate_xsts_token")
    @patch("apps.halo_infinite.tokens.get_user_token")
    def test_get_xsts_token(self, mock_get_user_token, mock_generate_xsts_token):
        in_memory_user_token = XboxLiveUserToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )

        # No token in DB results in HaloInfiniteXSTSTokenMissingException
        mock_get_user_token.return_value = in_memory_user_token
        mock_generate_xsts_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteXSTSTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteXSTSToken.",
            get_xsts_token,
        )
        mock_get_user_token.assert_called_once()
        mock_generate_xsts_token.assert_called_once_with(in_memory_user_token)
        mock_get_user_token.reset_mock()
        mock_generate_xsts_token.reset_mock()

        # Unexpired token in DB results in token being returned
        xsts_token = HaloInfiniteXSTSToken.objects.create(
            creator=self.user,
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )
        returned_xsts_token = get_xsts_token()
        self.assertEqual(returned_xsts_token.id, xsts_token.id)
        self.assertEqual(returned_xsts_token.token, xsts_token.token)
        self.assertEqual(returned_xsts_token.uhs, xsts_token.uhs)

        # Expired token in DB results in `generate_xsts_token` being called
        xsts_token.not_after = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=3600)
        xsts_token.save()
        new_xsts_token = HaloInfiniteXSTSToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="new_token",
            uhs="new_uhs",
        )
        mock_get_user_token.return_value = in_memory_user_token
        mock_generate_xsts_token.return_value = new_xsts_token
        returned_xsts_token = get_xsts_token()
        self.assertEqual(returned_xsts_token.token, new_xsts_token.token)
        self.assertEqual(returned_xsts_token.uhs, new_xsts_token.uhs)
        mock_generate_xsts_token.assert_called_once_with(in_memory_user_token)
        mock_get_user_token.reset_mock()
        mock_generate_xsts_token.reset_mock()

        # If new token generation method fails to create a new token, result is HaloInfiniteXSTSTokenMissingException
        mock_generate_xsts_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteXSTSTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteXSTSToken.",
            get_xsts_token,
        )

    @patch("apps.halo_infinite.tokens.requests.Session")
    def test_generate_spartan_token(self, mock_Session):
        xsts_token = HaloInfiniteXSTSToken.objects.create(
            creator=self.user,
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )

        # Successful status code should create another HaloInfiniteSpartanToken record with unique properties
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.post.return_value.json.return_value = {
            "SpartanToken": "test_spartan_token",
            "ExpiresUtc": {"ISO8601Date": "2023-02-23T08:23:26Z"},
            "TokenDuration": "test_duration",
        }
        new_spartan_token = generate_spartan_token(xsts_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://settings.svc.halowaypoint.com/spartan-token",
            json={
                "Audience": "urn:343:s3:services",
                "MinVersion": "4",
                "Proof": [{"Token": xsts_token.token, "TokenType": "Xbox_XSTSv3"}],
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
            },
        )
        self.assertEqual(HaloInfiniteSpartanToken.objects.all().count(), 1)
        self.assertIsNotNone(new_spartan_token.id)
        self.assertEqual(
            new_spartan_token.expires_utc,
            datetime.datetime(2023, 2, 23, 8, 23, 26, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(new_spartan_token.token, "test_spartan_token")
        self.assertEqual(new_spartan_token.token_duration, "test_duration")

        # Unsuccessful status code should return None and not create a new XboxLiveUserToken record
        mock_Session.reset_mock()
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            401
        )
        new_spartan_token = generate_spartan_token(xsts_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://settings.svc.halowaypoint.com/spartan-token",
            json={
                "Audience": "urn:343:s3:services",
                "MinVersion": "4",
                "Proof": [{"Token": xsts_token.token, "TokenType": "Xbox_XSTSv3"}],
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
            },
        )
        self.assertEqual(HaloInfiniteSpartanToken.objects.all().count(), 1)
        self.assertIsNone(new_spartan_token)

    @patch("apps.halo_infinite.tokens.generate_spartan_token")
    @patch("apps.halo_infinite.tokens.get_xsts_token")
    def test_get_spartan_token(self, mock_get_xsts_token, mock_generate_spartan_token):
        in_memory_xsts_token = HaloInfiniteXSTSToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )

        # No token in DB results in HaloInfiniteSpartanTokenMissingException
        mock_get_xsts_token.return_value = in_memory_xsts_token
        mock_generate_spartan_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteSpartanTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteSpartanToken.",
            get_spartan_token,
        )
        mock_get_xsts_token.assert_called_once()
        mock_generate_spartan_token.assert_called_once_with(in_memory_xsts_token)
        mock_get_xsts_token.reset_mock()
        mock_generate_spartan_token.reset_mock()

        # Unexpired token in DB results in token being returned
        spartan_token = HaloInfiniteSpartanToken.objects.create(
            creator=self.user,
            expires_utc=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="new_token",
            token_duration="new_duration",
        )
        returned_spartan_token = get_spartan_token()
        self.assertEqual(returned_spartan_token.id, spartan_token.id)
        self.assertEqual(returned_spartan_token.expires_utc, spartan_token.expires_utc)
        self.assertEqual(returned_spartan_token.token, spartan_token.token)
        self.assertEqual(
            returned_spartan_token.token_duration, spartan_token.token_duration
        )

        # Expired token in DB results in `generate_spartan_token` being called
        spartan_token.expires_utc = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=3600)
        spartan_token.save()
        new_spartan_token = HaloInfiniteSpartanToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            expires_utc=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="new_token",
            token_duration="new_duration",
        )
        mock_get_xsts_token.return_value = in_memory_xsts_token
        mock_generate_spartan_token.return_value = new_spartan_token
        returned_spartan_token = get_spartan_token()
        self.assertEqual(
            returned_spartan_token.expires_utc, new_spartan_token.expires_utc
        )
        self.assertEqual(returned_spartan_token.token, new_spartan_token.token)
        self.assertEqual(
            returned_spartan_token.token_duration, new_spartan_token.token_duration
        )
        mock_generate_spartan_token.assert_called_once_with(in_memory_xsts_token)
        mock_get_xsts_token.reset_mock()
        mock_generate_spartan_token.reset_mock()

        # If new token generation method fails to create a new token, result is HaloInfiniteSpartanTokenMissingException
        mock_generate_spartan_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteSpartanTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteSpartanToken.",
            get_spartan_token,
        )
