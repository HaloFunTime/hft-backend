import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.xbox_live.exceptions import (
    XboxLiveOAuthTokenMissingException,
    XboxLiveUserTokenMissingException,
    XboxLiveXSTSTokenMissingException,
)
from apps.xbox_live.models import (
    XboxLiveAccount,
    XboxLiveOAuthToken,
    XboxLiveUserToken,
    XboxLiveXSTSToken,
)
from apps.xbox_live.tokens import (
    generate_user_token,
    generate_xsts_token,
    get_oauth_token,
    get_user_token,
    get_xsts_token,
    refresh_oauth_token,
)
from apps.xbox_live.utils import get_xuid_for_gamertag


class XboxLiveAccountTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_xbox_live_account_save(self):
        # Creating an account should be successful
        account = XboxLiveAccount.objects.create(
            creator=self.user, gamertag="test", xuid=0
        )
        self.assertEqual(account.xuid, 0)
        self.assertEqual(account.gamertag, "test")

        # Duplicate XUID should fail to save
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "XboxLiveAccount_pkey"',
            lambda: XboxLiveAccount.objects.create(
                creator=self.user, gamertag="test", xuid=0
            ),
        )


class XboxLiveTokensTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.xbox_live.utils.requests.Session")
    def test_refresh_oauth_token(self, mock_Session):
        oauth_token = XboxLiveOAuthToken.objects.create(
            creator=self.user,
            token_type="bearer",
            expires_in=3600,
            scope="XboxLive.signin XboxLive.offline_access",
            access_token="first_access_token",
            refresh_token="first_refresh_token",
            user_id="user_id",
        )

        # Successful status code should create another XboxLiveOAuthToken record with unique properties
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.post.return_value.json.return_value = {
            "token_type": "bearer",
            "expires_in": 3600,
            "scope": "XboxLive.signin XboxLive.offline_access",
            "access_token": "second_access_token",
            "refresh_token": "second_refresh_token",
            "user_id": "user_id",
        }
        new_oauth_token = refresh_oauth_token(oauth_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://login.live.com/oauth20_token.srf",
            data={
                "grant_type": "refresh_token",
                "refresh_token": oauth_token.refresh_token,
                "approval_prompt": "auto",
                "redirect_uri": "http://localhost/auth/callback",
                "client_id": settings.AZURE_CLIENT_ID,
                "client_secret": settings.AZURE_CLIENT_SECRET,
                "scope": oauth_token.scope,
            },
        )
        self.assertEqual(XboxLiveOAuthToken.objects.all().count(), 2)
        self.assertNotEqual(oauth_token.id, new_oauth_token.id)
        self.assertNotEqual(oauth_token.access_token, new_oauth_token.access_token)
        self.assertNotEqual(oauth_token.refresh_token, new_oauth_token.refresh_token)

        # Unsuccessful status code should return None and not create a new XboxLiveOAuthToken record
        mock_Session.reset_mock()
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            401
        )
        new_oauth_token = refresh_oauth_token(oauth_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://login.live.com/oauth20_token.srf",
            data={
                "grant_type": "refresh_token",
                "refresh_token": oauth_token.refresh_token,
                "approval_prompt": "auto",
                "redirect_uri": "http://localhost/auth/callback",
                "client_id": settings.AZURE_CLIENT_ID,
                "client_secret": settings.AZURE_CLIENT_SECRET,
                "scope": oauth_token.scope,
            },
        )
        self.assertEqual(XboxLiveOAuthToken.objects.all().count(), 2)
        self.assertIsNone(new_oauth_token)

    @patch("apps.xbox_live.tokens.refresh_oauth_token")
    def test_get_oauth_token(self, mock_refresh_oauth_token):
        # No token in DB results in XboxLiveOAuthTokenMissingException
        self.assertRaisesMessage(
            XboxLiveOAuthTokenMissingException,
            "Could not retrieve an unexpired XboxLiveOAuthToken.",
            get_oauth_token,
        )

        # Unexpired token in DB results in token being returned
        oauth_token = XboxLiveOAuthToken.objects.create(
            creator=self.user,
            token_type="bearer",
            expires_in=3600,
            scope="XboxLive.signin XboxLive.offline_access",
            access_token="first_access_token",
            refresh_token="first_refresh_token",
            user_id="user_id",
        )
        returned_oauth_token = get_oauth_token()
        self.assertEqual(returned_oauth_token.id, oauth_token.id)
        self.assertEqual(returned_oauth_token.access_token, oauth_token.access_token)
        self.assertEqual(returned_oauth_token.refresh_token, oauth_token.refresh_token)

        # Expired token in DB results in `refresh_oauth_token` being called
        oauth_token.created_at = oauth_token.created_at - datetime.timedelta(
            seconds=(oauth_token.expires_in + 1)
        )
        oauth_token.save()
        fresh_oauth_token = XboxLiveOAuthToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            token_type="bearer",
            expires_in=3600,
            scope="XboxLive.signin XboxLive.offline_access",
            access_token="second_access_token",
            refresh_token="second_refresh_token",
            user_id="user_id",
        )
        mock_refresh_oauth_token.return_value = fresh_oauth_token
        returned_oauth_token = get_oauth_token()
        self.assertEqual(
            returned_oauth_token.access_token, fresh_oauth_token.access_token
        )
        self.assertEqual(
            returned_oauth_token.refresh_token, fresh_oauth_token.refresh_token
        )
        mock_refresh_oauth_token.assert_called_once_with(oauth_token)
        mock_refresh_oauth_token.reset_mock()

        # If refresh method fails to create a new token, result is an XboxLiveOAuthTokenMissingException
        mock_refresh_oauth_token.return_value = None
        self.assertRaisesMessage(
            XboxLiveOAuthTokenMissingException,
            "Could not retrieve an unexpired XboxLiveOAuthToken.",
            get_oauth_token,
        )

    @patch("apps.xbox_live.utils.requests.Session")
    def test_generate_user_token(self, mock_Session):
        oauth_token = XboxLiveOAuthToken.objects.create(
            creator=self.user,
            token_type="bearer",
            expires_in=3600,
            scope="XboxLive.signin XboxLive.offline_access",
            access_token="access_token",
            refresh_token="refresh_token",
            user_id="user_id",
        )

        # Successful status code should create another XboxLiveOAuthToken record with unique properties
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.post.return_value.json.return_value = {
            "IssueInstant": "2023-02-14T04:22:12.7916353Z",
            "NotAfter": "2023-02-28T04:22:12.7916353Z",
            "Token": "test_token",
            "DisplayClaims": {"xui": [{"uhs": "test_uhs"}]},
        }
        new_user_token = generate_user_token(oauth_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://user.auth.xboxlive.com/user/authenticate",
            json={
                "Properties": {
                    "AuthMethod": "RPS",
                    "RpsTicket": f"d={oauth_token.access_token}",
                    "SiteName": "user.auth.xboxlive.com",
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(XboxLiveUserToken.objects.all().count(), 1)
        self.assertIsNotNone(new_user_token.id)
        self.assertEqual(
            new_user_token.issue_instant,
            datetime.datetime(2023, 2, 14, 4, 22, 12, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(
            new_user_token.not_after,
            datetime.datetime(2023, 2, 28, 4, 22, 12, tzinfo=datetime.timezone.utc),
        )
        self.assertEqual(new_user_token.token, "test_token")
        self.assertEqual(new_user_token.uhs, "test_uhs")

        # Unsuccessful status code should return None and not create a new XboxLiveUserToken record
        mock_Session.reset_mock()
        mock_Session.return_value.__enter__.return_value.post.return_value.status_code = (
            401
        )
        new_user_token = generate_user_token(oauth_token)
        mock_Session.return_value.__enter__.return_value.post.assert_called_once_with(
            "https://user.auth.xboxlive.com/user/authenticate",
            json={
                "Properties": {
                    "AuthMethod": "RPS",
                    "RpsTicket": f"d={oauth_token.access_token}",
                    "SiteName": "user.auth.xboxlive.com",
                },
                "RelyingParty": "http://auth.xboxlive.com",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(XboxLiveUserToken.objects.all().count(), 1)
        self.assertIsNone(new_user_token)

    @patch("apps.xbox_live.tokens.generate_user_token")
    @patch("apps.xbox_live.tokens.get_oauth_token")
    def test_get_user_token(self, mock_get_oauth_token, mock_generate_user_token):
        in_memory_oauth_token = XboxLiveOAuthToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            token_type="bearer",
            expires_in=3600,
            scope="XboxLive.signin XboxLive.offline_access",
            access_token="access_token",
            refresh_token="refresh_token",
            user_id="user_id",
        )

        # No token in DB results in XboxLiveUserTokenMissingException
        mock_get_oauth_token.return_value = in_memory_oauth_token
        mock_generate_user_token.return_value = None
        self.assertRaisesMessage(
            XboxLiveUserTokenMissingException,
            "Could not retrieve an unexpired XboxLiveUserToken.",
            get_user_token,
        )
        mock_get_oauth_token.assert_called_once()
        mock_generate_user_token.assert_called_once_with(in_memory_oauth_token)
        mock_get_oauth_token.reset_mock()
        mock_generate_user_token.reset_mock()

        # Unexpired token in DB results in token being returned
        user_token = XboxLiveUserToken.objects.create(
            creator=self.user,
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )
        returned_user_token = get_user_token()
        self.assertEqual(returned_user_token.id, user_token.id)
        self.assertEqual(returned_user_token.token, user_token.token)
        self.assertEqual(returned_user_token.uhs, user_token.uhs)

        # Expired token in DB results in `generate_user_token` being called
        user_token.not_after = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=3600)
        user_token.save()
        new_user_token = XboxLiveUserToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="new_token",
            uhs="new_uhs",
        )
        mock_get_oauth_token.return_value = in_memory_oauth_token
        mock_generate_user_token.return_value = new_user_token
        returned_user_token = get_user_token()
        self.assertEqual(returned_user_token.token, new_user_token.token)
        self.assertEqual(returned_user_token.uhs, new_user_token.uhs)
        mock_generate_user_token.assert_called_once_with(in_memory_oauth_token)
        mock_get_oauth_token.reset_mock()
        mock_generate_user_token.reset_mock()

        # If new token generation method fails to create a new token, result is an XboxLiveUserTokenMissingException
        mock_generate_user_token.return_value = None
        self.assertRaisesMessage(
            XboxLiveUserTokenMissingException,
            "Could not retrieve an unexpired XboxLiveUserToken.",
            get_user_token,
        )

    @patch("apps.xbox_live.utils.requests.Session")
    def test_generate_xsts_token(self, mock_Session):
        user_token = XboxLiveUserToken.objects.create(
            creator=self.user,
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            uhs="test_uhs",
        )

        # Successful status code should create another XboxLiveOAuthToken record with unique properties
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
                "RelyingParty": "http://xboxlive.com",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(XboxLiveXSTSToken.objects.all().count(), 1)
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
                "RelyingParty": "http://xboxlive.com",
                "TokenType": "JWT",
            },
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "1",
            },
        )
        self.assertEqual(XboxLiveXSTSToken.objects.all().count(), 1)
        self.assertIsNone(new_xsts_token)

    @patch("apps.xbox_live.tokens.generate_xsts_token")
    @patch("apps.xbox_live.tokens.get_user_token")
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

        # No token in DB results in XboxLiveXSTSTokenMissingException
        mock_get_user_token.return_value = in_memory_user_token
        mock_generate_xsts_token.return_value = None
        self.assertRaisesMessage(
            XboxLiveXSTSTokenMissingException,
            "Could not retrieve an unexpired XboxLiveXSTSToken.",
            get_xsts_token,
        )
        mock_get_user_token.assert_called_once()
        mock_generate_xsts_token.assert_called_once_with(in_memory_user_token)
        mock_get_user_token.reset_mock()
        mock_generate_xsts_token.reset_mock()

        # Unexpired token in DB results in token being returned
        xsts_token = XboxLiveXSTSToken.objects.create(
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
        new_xsts_token = XboxLiveXSTSToken(
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

        # If new token generation method fails to create a new token, result is an XboxLiveXSTSTokenMissingException
        mock_generate_xsts_token.return_value = None
        self.assertRaisesMessage(
            XboxLiveXSTSTokenMissingException,
            "Could not retrieve an unexpired XboxLiveXSTSToken.",
            get_xsts_token,
        )


class XboxLiveUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.xbox_live.utils.requests.Session")
    @patch("apps.xbox_live.decorators.get_xsts_token")
    def test_get_xuid_for_gamertag(self, mock_get_xsts_token, mock_Session):
        # Test a successful call
        mock_get_xsts_token.return_value = XboxLiveXSTSToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="token",
            uhs="uhs",
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "profileUsers": [
                {
                    "id": "2535405290989773",
                    "hostId": "2535405290989773",
                    "settings": [],
                    "isSponsoredUser": False,
                }
            ]
        }
        xuid = get_xuid_for_gamertag("HFT Intern")
        self.assertEqual(xuid, "2535405290989773")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://profile.xboxlive.com/users/gt(HFT Intern)/profile/settings",
            headers={
                "Authorization": "XBL3.0 x=uhs;token",
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "3",
            },
        )
        mock_get_xsts_token.reset_mock()
        mock_Session.reset_mock()

        # Test a failed call
        mock_get_xsts_token.return_value = XboxLiveXSTSToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            issue_instant=datetime.datetime.now(datetime.timezone.utc),
            not_after=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="token",
            uhs="uhs",
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "code": 28,
            "source": "Profile",
            "description": "The server found no data for the requested entity.",
            "traceInformation": None,
        }
        xuid = get_xuid_for_gamertag("HFT Intern")
        self.assertIsNone(xuid)
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://profile.xboxlive.com/users/gt(HFT Intern)/profile/settings",
            headers={
                "Authorization": "XBL3.0 x=uhs;token",
                "Content-Type": "application/json; charset=utf-8",
                "x-xbl-contract-version": "3",
            },
        )
        mock_get_xsts_token.reset_mock()
        mock_Session.reset_mock()
