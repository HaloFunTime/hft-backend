import datetime
import uuid
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.test import TestCase

from apps.halo_infinite.exceptions import (
    HaloInfiniteClearanceTokenMissingException,
    HaloInfiniteSpartanTokenMissingException,
    HaloInfiniteXSTSTokenMissingException,
)
from apps.halo_infinite.models import (
    HaloInfiniteBuildID,
    HaloInfiniteClearanceToken,
    HaloInfinitePlaylist,
    HaloInfiniteSpartanToken,
    HaloInfiniteXSTSToken,
)
from apps.halo_infinite.tokens import (
    generate_clearance_token,
    generate_spartan_token,
    generate_xsts_token,
    get_clearance_token,
    get_spartan_token,
    get_xsts_token,
)
from apps.halo_infinite.utils import (
    SEARCH_ASSET_KIND_MAP,
    SEARCH_ASSET_KIND_MODE,
    SEARCH_ASSET_KIND_PREFAB,
    SEASON_DAYS_AND_TIMES,
    get_343_recommended_contributors,
    get_authored_maps,
    get_authored_modes,
    get_authored_prefabs,
    get_csr_after_match,
    get_csrs,
    get_playlist_latest_version_info,
    get_ranked_arena_playlist_id_for_season,
    get_season_custom_matches_for_xuid,
    get_season_ranked_arena_matches_for_xuid,
    get_start_and_end_times_for_season,
    get_summary_stats,
)
from apps.xbox_live.models import XboxLiveUserToken


class HaloInfinitePlaylistTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.halo_infinite.signals.get_playlist_latest_version_info")
    def test_halo_infinite_playlist_save(self, mock_get_playlist_latest_version_info):
        # Creating a playlist should be successful if only Playlist ID is provided (rest is hydrated by pre_save)
        test_1_playlist_id = uuid.uuid4()
        test_1_version_id = uuid.uuid4()
        mock_get_playlist_latest_version_info.return_value = {
            "playlist_id": test_1_playlist_id,
            "version_id": test_1_version_id,
            "ranked": True,
            "name": "name",
            "description": "description",
        }
        playlist = HaloInfinitePlaylist.objects.create(
            creator=self.user, playlist_id=test_1_playlist_id
        )
        self.assertEqual(playlist.playlist_id, test_1_playlist_id)
        self.assertEqual(playlist.version_id, test_1_version_id)
        self.assertEqual(playlist.ranked, True)
        self.assertEqual(playlist.name, "name")
        self.assertEqual(playlist.description, "description")

        mock_get_playlist_latest_version_info.assert_called_once_with(
            test_1_playlist_id
        )
        mock_get_playlist_latest_version_info.reset_mock()

        # Playlist ID provided in create call should be replaced by the one retrieved in pre_save signal
        test_2_playlist_id = uuid.uuid4()
        test_2_version_id = uuid.uuid4()
        mock_get_playlist_latest_version_info.return_value = {
            "playlist_id": test_2_playlist_id,
            "version_id": test_2_version_id,
            "ranked": False,
            "name": "test_name",
            "description": "test_description",
        }
        playlist = HaloInfinitePlaylist.objects.create(
            creator=self.user, playlist_id="test_wrong_playlist_id"
        )
        self.assertEqual(playlist.playlist_id, test_2_playlist_id)
        self.assertEqual(playlist.version_id, test_2_version_id)
        self.assertEqual(playlist.ranked, False)
        self.assertEqual(playlist.name, "test_name")
        self.assertEqual(playlist.description, "test_description")
        mock_get_playlist_latest_version_info.assert_called_once_with(
            "test_wrong_playlist_id"
        )
        mock_get_playlist_latest_version_info.reset_mock()

        # Duplicate Playlist ID should fail to save
        mock_get_playlist_latest_version_info.return_value = {
            "playlist_id": test_1_playlist_id,
            "version_id": test_1_version_id,
            "ranked": True,
            "name": "test_name",
            "description": "test_description",
        }
        self.assertRaisesMessage(
            IntegrityError,
            'duplicate key value violates unique constraint "HaloInfinitePlaylist_pkey"',
            lambda: HaloInfinitePlaylist.objects.create(
                creator=self.user, playlist_id=test_1_playlist_id
            ),
        )
        mock_get_playlist_latest_version_info.assert_called_once_with(
            test_1_playlist_id
        )
        mock_get_playlist_latest_version_info.reset_mock()


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

        # If new token generation method fails to create a new token, HaloInfiniteXSTSTokenMissingException
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
            201
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

        # If new token generation method fails to create a new token, HaloInfiniteSpartanTokenMissingException
        mock_generate_spartan_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteSpartanTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteSpartanToken.",
            get_spartan_token,
        )

    @patch("apps.halo_infinite.tokens.requests.Session")
    def test_generate_clearance_token(self, mock_Session):
        spartan_token = HaloInfiniteSpartanToken.objects.create(
            creator=self.user,
            expires_utc=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="new_token",
            token_duration="new_duration",
        )

        # Successful status code should create another HaloInfiniteClearanceToken record with unique properties
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "FlightConfigurationId": "test_clearance_token"
        }
        test_xuid = "1234"
        test_build_id = "v1.0.0"
        new_clearance_token = generate_clearance_token(
            spartan_token, test_xuid, test_build_id
        )
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://settings.svc.halowaypoint.com/oban/flight-configurations/titles/hi/audiences/RETAIL/players/"
            f"xuid({test_xuid})/active?sandbox=UNUSED&build={test_build_id}",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": spartan_token.token,
            },
        )
        self.assertEqual(HaloInfiniteClearanceToken.objects.all().count(), 1)
        self.assertIsNotNone(new_clearance_token.id)
        self.assertEqual(
            new_clearance_token.flight_configuration_id, "test_clearance_token"
        )

        # Unsuccessful status code should return None and not create a new XboxLiveUserToken record
        mock_Session.reset_mock()
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            401
        )
        test_xuid = "1234"
        test_build_id = "v1.0.0"
        new_clearance_token = generate_clearance_token(
            spartan_token, test_xuid, test_build_id
        )
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://settings.svc.halowaypoint.com/oban/flight-configurations/titles/hi/audiences/RETAIL/players/"
            f"xuid({test_xuid})/active?sandbox=UNUSED&build={test_build_id}",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": spartan_token.token,
            },
        )
        self.assertEqual(HaloInfiniteClearanceToken.objects.all().count(), 1)
        self.assertIsNone(new_clearance_token)

    @patch("apps.halo_infinite.tokens.generate_clearance_token")
    @patch("apps.halo_infinite.tokens.get_spartan_token")
    def test_get_clearance_token(
        self, mock_get_spartan_token, mock_generate_clearance_token
    ):
        in_memory_spartan_token = HaloInfiniteSpartanToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            expires_utc=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=3600),
            token="test_token",
            token_duration="test_duration",
        )
        test_build_id = HaloInfiniteBuildID.objects.create(
            creator=self.user,
            build_date=datetime.datetime.now(datetime.timezone.utc),
            build_id="1.0.0",
        )

        # No token in DB results in HaloInfiniteClearanceTokenMissingException
        mock_get_spartan_token.return_value = in_memory_spartan_token
        mock_generate_clearance_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteClearanceTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteClearanceToken.",
            get_clearance_token,
        )
        mock_get_spartan_token.assert_called_once()
        mock_generate_clearance_token.assert_called_once_with(
            in_memory_spartan_token, settings.INTERN_XUID, test_build_id.build_id
        )
        mock_get_spartan_token.reset_mock()
        mock_generate_clearance_token.reset_mock()

        # Unexpired token in DB results in token being returned
        clearance_token = HaloInfiniteClearanceToken.objects.create(
            creator=self.user,
            flight_configuration_id="test_clearance",
        )
        returned_clearance_token = get_clearance_token()
        self.assertEqual(returned_clearance_token.id, clearance_token.id)
        self.assertEqual(
            returned_clearance_token.flight_configuration_id,
            clearance_token.flight_configuration_id,
        )

        # Expired token in DB results in `generate_clearance_token` being called
        clearance_token.created_at = datetime.datetime.now(
            datetime.timezone.utc
        ) - datetime.timedelta(seconds=3600)
        clearance_token.save()
        new_clearance_token = HaloInfiniteClearanceToken(
            creator=self.user,
            created_at=datetime.datetime.now(datetime.timezone.utc),
            updated_at=datetime.datetime.now(datetime.timezone.utc),
            flight_configuration_id="new_clearance",
        )
        mock_get_spartan_token.return_value = in_memory_spartan_token
        mock_generate_clearance_token.return_value = new_clearance_token
        returned_clearance_token = get_clearance_token()
        self.assertEqual(returned_clearance_token.id, new_clearance_token.id)
        self.assertEqual(
            returned_clearance_token.flight_configuration_id,
            new_clearance_token.flight_configuration_id,
        )
        mock_generate_clearance_token.assert_called_once_with(
            in_memory_spartan_token, settings.INTERN_XUID, test_build_id.build_id
        )
        mock_get_spartan_token.reset_mock()
        mock_generate_clearance_token.reset_mock()

        # If new token generation method fails to create a new token, HaloInfiniteClearanceTokenMissingException
        mock_generate_clearance_token.return_value = None
        self.assertRaisesMessage(
            HaloInfiniteClearanceTokenMissingException,
            "Could not retrieve an unexpired HaloInfiniteClearanceToken.",
            get_clearance_token,
        )


class HaloInfiniteUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    @patch("apps.halo_infinite.utils.recommended")
    def test_get_343_recommended_contributors(self, mock_recommended):
        mock_recommended.return_value = {
            "MapLinks": [
                {
                    "Contributors": [
                        "xuid(2814660312652330)",
                        "xuid(2533274795021402)",
                        "xuid(2535425050848538)",
                        "xuid(2533274801987300)",
                        "xuid(2533274835876334)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2533274873806365)",
                        "xuid(2533274906188134)",
                        "xuid(2533274831077797)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2535419870450908)",
                        "xuid(2533274968441932)",
                        "xuid(2535472198826651)",
                        "xuid(2533274876991706)",
                        "xuid(2535427784773192)",
                        "xuid(2533274825961918)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2599622463478870)",
                        "xuid(2533274839415478)",
                        "xuid(2535417458493667)",
                        "xuid(2533274835876334)",
                        "xuid(2533274807200960)",
                        "xuid(2535406614685708)",
                    ],
                },
            ],
            "UgcGameVariantLinks": [
                {
                    "Contributors": [
                        "xuid(2814660312652330)",
                        "xuid(2533274795021402)",
                        "xuid(2535425050848538)",
                        "xuid(2533274801987300)",
                        "xuid(2533274835876334)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2533274873806365)",
                        "xuid(2533274906188134)",
                        "xuid(2533274831077797)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2535419870450908)",
                        "xuid(2533274968441932)",
                        "xuid(2535472198826651)",
                        "xuid(2533274876991706)",
                        "xuid(2535427784773192)",
                        "xuid(2533274825961918)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2599622463478870)",
                        "xuid(2533274839415478)",
                        "xuid(2535417458493667)",
                        "xuid(2533274835876334)",
                        "xuid(2533274807200960)",
                        "xuid(2535406614685708)",
                    ],
                },
            ],
            "PrefabLinks": [
                {
                    "Contributors": [
                        "xuid(2814660312652330)",
                        "xuid(2533274795021402)",
                        "xuid(2535425050848538)",
                        "xuid(2533274801987300)",
                        "xuid(2533274835876334)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2533274873806365)",
                        "xuid(2533274906188134)",
                        "xuid(2533274831077797)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2535419870450908)",
                        "xuid(2533274968441932)",
                        "xuid(2535472198826651)",
                        "xuid(2533274876991706)",
                        "xuid(2535427784773192)",
                        "xuid(2533274825961918)",
                        "xuid(2535406614685708)",
                    ],
                },
                {
                    "Contributors": [
                        "xuid(2599622463478870)",
                        "xuid(2533274839415478)",
                        "xuid(2535417458493667)",
                        "xuid(2533274835876334)",
                        "xuid(2533274807200960)",
                        "xuid(2535406614685708)",
                    ],
                },
            ],
        }
        data = get_343_recommended_contributors()
        self.assertEqual(data.get("map").get(2814660312652330), 1)
        self.assertEqual(data.get("map").get(2533274795021402), 1)
        self.assertEqual(data.get("map").get(2535425050848538), 1)
        self.assertEqual(data.get("map").get(2533274801987300), 1)
        self.assertEqual(data.get("map").get(2533274835876334), 2)
        self.assertEqual(data.get("map").get(2535406614685708), 4)
        self.assertEqual(data.get("map").get(2533274873806365), 1)
        self.assertEqual(data.get("map").get(2533274906188134), 1)
        self.assertEqual(data.get("map").get(2533274831077797), 1)
        self.assertEqual(data.get("map").get(2535419870450908), 1)
        self.assertEqual(data.get("map").get(2533274968441932), 1)
        self.assertEqual(data.get("map").get(2535472198826651), 1)
        self.assertEqual(data.get("map").get(2533274876991706), 1)
        self.assertEqual(data.get("map").get(2535427784773192), 1)
        self.assertEqual(data.get("map").get(2533274825961918), 1)
        self.assertEqual(data.get("map").get(2599622463478870), 1)
        self.assertEqual(data.get("map").get(2533274839415478), 1)
        self.assertEqual(data.get("map").get(2535417458493667), 1)
        self.assertEqual(data.get("map").get(2533274807200960), 1)
        self.assertEqual(data.get("mode").get(2814660312652330), 1)
        self.assertEqual(data.get("mode").get(2533274795021402), 1)
        self.assertEqual(data.get("mode").get(2535425050848538), 1)
        self.assertEqual(data.get("mode").get(2533274801987300), 1)
        self.assertEqual(data.get("mode").get(2533274835876334), 2)
        self.assertEqual(data.get("mode").get(2535406614685708), 4)
        self.assertEqual(data.get("mode").get(2533274873806365), 1)
        self.assertEqual(data.get("mode").get(2533274906188134), 1)
        self.assertEqual(data.get("mode").get(2533274831077797), 1)
        self.assertEqual(data.get("mode").get(2535419870450908), 1)
        self.assertEqual(data.get("mode").get(2533274968441932), 1)
        self.assertEqual(data.get("mode").get(2535472198826651), 1)
        self.assertEqual(data.get("mode").get(2533274876991706), 1)
        self.assertEqual(data.get("mode").get(2535427784773192), 1)
        self.assertEqual(data.get("mode").get(2533274825961918), 1)
        self.assertEqual(data.get("mode").get(2599622463478870), 1)
        self.assertEqual(data.get("mode").get(2533274839415478), 1)
        self.assertEqual(data.get("mode").get(2535417458493667), 1)
        self.assertEqual(data.get("mode").get(2533274807200960), 1)
        self.assertEqual(data.get("prefab").get(2814660312652330), 1)
        self.assertEqual(data.get("prefab").get(2533274795021402), 1)
        self.assertEqual(data.get("prefab").get(2535425050848538), 1)
        self.assertEqual(data.get("prefab").get(2533274801987300), 1)
        self.assertEqual(data.get("prefab").get(2533274835876334), 2)
        self.assertEqual(data.get("prefab").get(2535406614685708), 4)
        self.assertEqual(data.get("prefab").get(2533274873806365), 1)
        self.assertEqual(data.get("prefab").get(2533274906188134), 1)
        self.assertEqual(data.get("prefab").get(2533274831077797), 1)
        self.assertEqual(data.get("prefab").get(2535419870450908), 1)
        self.assertEqual(data.get("prefab").get(2533274968441932), 1)
        self.assertEqual(data.get("prefab").get(2535472198826651), 1)
        self.assertEqual(data.get("prefab").get(2533274876991706), 1)
        self.assertEqual(data.get("prefab").get(2535427784773192), 1)
        self.assertEqual(data.get("prefab").get(2533274825961918), 1)
        self.assertEqual(data.get("prefab").get(2599622463478870), 1)
        self.assertEqual(data.get("prefab").get(2533274839415478), 1)
        self.assertEqual(data.get("prefab").get(2535417458493667), 1)
        self.assertEqual(data.get("prefab").get(2533274807200960), 1)
        mock_recommended.assert_called_once_with()

    @patch("apps.halo_infinite.utils.search_by_author")
    def test_get_authored_maps(self, mock_search_by_author):
        mock_search_by_author.return_value = []
        data = get_authored_maps(0)
        self.assertEqual(data, [])

        mock_search_by_author.return_value = [
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_PREFAB},
        ]
        data = get_authored_maps(0)
        self.assertEqual(len(data), 3)
        self.assertEqual(
            data,
            [
                {"AssetKind": SEARCH_ASSET_KIND_MAP},
                {"AssetKind": SEARCH_ASSET_KIND_MAP},
                {"AssetKind": SEARCH_ASSET_KIND_MAP},
            ],
        )

    @patch("apps.halo_infinite.utils.search_by_author")
    def test_get_authored_modes(self, mock_search_by_author):
        mock_search_by_author.return_value = []
        data = get_authored_modes(0)
        self.assertEqual(data, [])

        mock_search_by_author.return_value = [
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_PREFAB},
        ]
        data = get_authored_modes(0)
        self.assertEqual(len(data), 2)
        self.assertEqual(
            data,
            [
                {"AssetKind": SEARCH_ASSET_KIND_MODE},
                {"AssetKind": SEARCH_ASSET_KIND_MODE},
            ],
        )

    @patch("apps.halo_infinite.utils.search_by_author")
    def test_get_authored_prefabs(self, mock_search_by_author):
        mock_search_by_author.return_value = []
        data = get_authored_prefabs(0)
        self.assertEqual(data, [])

        mock_search_by_author.return_value = [
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MAP},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_MODE},
            {"AssetKind": SEARCH_ASSET_KIND_PREFAB},
        ]
        data = get_authored_prefabs(0)
        self.assertEqual(len(data), 1)
        self.assertEqual(
            data,
            [
                {"AssetKind": SEARCH_ASSET_KIND_PREFAB},
            ],
        )

    @patch("apps.halo_infinite.utils.csr")
    def test_get_csrs(self, mock_csr):
        mock_csr.return_value = {
            "Value": [
                {
                    "Id": "xuid(2533274870001169)",
                    "ResultCode": 0,
                    "Result": {
                        "Current": {
                            "Value": 1498,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Diamond",
                            "TierStart": 1200,
                            "SubTier": 5,
                            "NextTier": "Onyx",
                            "NextTierStart": 1500,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                        "SeasonMax": {
                            "Value": 1573,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Onyx",
                            "TierStart": 1500,
                            "SubTier": 0,
                            "NextTier": "Onyx",
                            "NextTierStart": 1500,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                        "AllTimeMax": {
                            "Value": 1683,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Onyx",
                            "TierStart": 1500,
                            "SubTier": 0,
                            "NextTier": "Onyx",
                            "NextTierStart": 1500,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                    },
                }
            ]
        }
        data = get_csrs([2533274870001169], "test_playlist_id")
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_csr"), 1498
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_tier"), "Diamond"
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_subtier"), 6
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_tier_description"),
            "Diamond 6",
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_reset_max_csr"), 1573
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_reset_max_tier"),
            "Onyx",
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("current_reset_max_subtier"), 1
        )
        self.assertEqual(
            data.get("csrs")
            .get(2533274870001169)
            .get("current_reset_max_tier_description"),
            "Onyx",
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("all_time_max_csr"), 1683
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("all_time_max_tier"), "Onyx"
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("all_time_max_subtier"), 1
        )
        self.assertEqual(
            data.get("csrs").get(2533274870001169).get("all_time_max_tier_description"),
            "Onyx",
        )
        mock_csr.assert_called_once_with([2533274870001169], "test_playlist_id")

    @patch("apps.halo_infinite.utils.match_skill")
    def test_get_csr_after_match(self, mock_match_skill):
        mock_match_skill.return_value = {
            "Value": [{"Result": {"RankRecap": {"PostMatchCsr": {"Value": 1234}}}}]
        }
        result_csr = get_csr_after_match(123, "abc")
        self.assertEqual(result_csr, 1234)
        mock_match_skill.assert_called_once_with(123, "abc")
        mock_match_skill.reset_mock()

        mock_match_skill.return_value = {}
        result_csr = get_csr_after_match(456, "def")
        self.assertEqual(result_csr, -1)
        mock_match_skill.assert_called_once_with(456, "def")
        mock_match_skill.reset_mock()

    @patch("apps.halo_infinite.utils.playlist_version")
    @patch("apps.halo_infinite.utils.playlist_info")
    def test_get_playlist_latest_version_info(
        self, mock_playlist_info, mock_playlist_version
    ):
        mock_playlist_info.return_value = {
            "UgcPlaylistVersion": "test_version_id",
            "HasCsr": True,
        }
        mock_playlist_version.return_value = {
            "AssetId": "return_playlist_id",
            "VersionId": "return_version_id",
            "PublicName": "Test Name",
            "Description": "Test Description",
        }
        data = get_playlist_latest_version_info("test_playlist_id")
        self.assertEqual(data.get("playlist_id"), "return_playlist_id")
        self.assertEqual(data.get("version_id"), "return_version_id")
        self.assertEqual(data.get("ranked"), True)
        self.assertEqual(data.get("name"), "Test Name")
        self.assertEqual(data.get("description"), "Test Description")
        mock_playlist_info.assert_called_once_with("test_playlist_id")
        mock_playlist_version.assert_called_once_with(
            "test_playlist_id", "test_version_id"
        )

    @patch("apps.halo_infinite.utils.matches_between")
    def test_get_get_season_custom_matches_for_xuid(self, mock_matches_between):
        for season_id in SEASON_DAYS_AND_TIMES.keys():
            start_time, end_time = get_start_and_end_times_for_season(season_id)
            mock_matches_between.return_value = [
                {"MatchId": "foo"},
                {"MatchId": "bar"},
                {"MatchId": "baz"},
            ]
            season_custom_matches = get_season_custom_matches_for_xuid(season_id, 123)
            self.assertEqual(len(season_custom_matches), 3)
            mock_matches_between.assert_called_once_with(
                123, start_time, end_time, "Custom"
            )
            mock_matches_between.reset_mock()

    @patch("apps.halo_infinite.utils.matches_between")
    def test_get_season_ranked_arena_matches_for_xuid(self, mock_matches_between):
        for season_id in SEASON_DAYS_AND_TIMES.keys():
            start_time, end_time = get_start_and_end_times_for_season(season_id)
            ranked_arena_playlist_id = get_ranked_arena_playlist_id_for_season(
                season_id
            )
            mock_matches_between.return_value = [
                {"MatchInfo": {"Playlist": {"AssetId": ranked_arena_playlist_id}}},
                {"MatchInfo": {"Playlist": {"AssetId": "wrong_playlist"}}},
                {"MatchInfo": {"Playlist": {"AssetId": ranked_arena_playlist_id}}},
            ]
            seasonal_ranked_arena_matches = get_season_ranked_arena_matches_for_xuid(
                season_id, 123
            )
            self.assertEqual(len(seasonal_ranked_arena_matches), 2)
            mock_matches_between.assert_called_once_with(
                123, start_time, end_time, "Matchmaking"
            )
            mock_matches_between.reset_mock()

    @patch("apps.halo_infinite.utils.match_count")
    @patch("apps.halo_infinite.utils.service_record")
    def test_get_summary_stats(self, mock_service_record, mock_match_count):
        mock_service_record.return_value = {
            "Wins": 1,
            "Losses": 2,
            "Ties": 3,
            "CoreStats": {"Kills": 4, "Deaths": 5, "Assists": 6, "AverageKDA": 7.89},
        }
        mock_match_count.return_value = {
            "MatchmadeMatchesPlayedCount": 10,
            "CustomMatchesPlayedCount": 11,
            "LocalMatchesPlayedCount": 12,
            "MatchesPlayedCount": 33,
        }
        data = get_summary_stats(0)
        self.assertEqual(data.get("matchmaking").get("wins"), 1)
        self.assertEqual(data.get("matchmaking").get("losses"), 2)
        self.assertEqual(data.get("matchmaking").get("ties"), 3)
        self.assertEqual(data.get("matchmaking").get("kills"), 4)
        self.assertEqual(data.get("matchmaking").get("deaths"), 5)
        self.assertEqual(data.get("matchmaking").get("assists"), 6)
        self.assertEqual(data.get("matchmaking").get("kda"), 7.89)
        self.assertEqual(data.get("matchmaking").get("games_played"), 10)
        self.assertEqual(data.get("custom").get("games_played"), 11)
        self.assertEqual(data.get("local").get("games_played"), 12)
        self.assertEqual(data.get("games_played"), 33)
        mock_service_record.assert_called_once_with(0)
        mock_match_count.assert_called_once_with(0)
