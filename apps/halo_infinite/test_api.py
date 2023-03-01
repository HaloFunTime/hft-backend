import datetime
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.halo_infinite.api.csr import csr
from apps.halo_infinite.api.match import match_count, match_privacy
from apps.halo_infinite.api.playlist import playlist_info, playlist_version
from apps.halo_infinite.api.service_record import service_record
from apps.halo_infinite.models import (
    HaloInfiniteClearanceToken,
    HaloInfiniteSpartanToken,
)


class HaloInfiniteAPITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        self.spartan_token = HaloInfiniteSpartanToken.objects.create(
            creator=self.user,
            expires_utc=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=86400),
            token="test_token",
            token_duration="test_duration",
        )
        self.clearance_token = HaloInfiniteClearanceToken.objects.create(
            creator=self.user,
            flight_configuration_id="test_clearance",
        )

    @patch("apps.halo_infinite.api.csr.requests.Session")
    def test_csr(self, mock_Session):
        # Successful call with one XUID
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "Value": [
                {
                    "Id": "xuid(2533274870001169)",
                    "ResultCode": 0,
                    "Result": {
                        "Current": {
                            "Value": 1513,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Onyx",
                            "TierStart": 1500,
                            "SubTier": 0,
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
        csr_data = csr([2533274870001169], "test_playlist_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://skill.svc.halowaypoint.com:443/hi/playlist/test_playlist_id/csrs?players=xuid(2533274870001169)",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
                "343-clearance": self.clearance_token.flight_configuration_id,
            },
        )
        self.assertIn("2533274870001169", csr_data.get("Value")[0].get("Id"))
        mock_Session.reset_mock()

        # Successful call with three XUIDs
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "Value": [
                {
                    "Id": "xuid(2535405290989773)",
                    "ResultCode": 0,
                    "Result": {
                        "Current": {
                            "Value": -1,
                            "MeasurementMatchesRemaining": 10,
                            "Tier": "",
                            "TierStart": 0,
                            "SubTier": 0,
                            "NextTier": "",
                            "NextTierStart": 0,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                        "SeasonMax": {
                            "Value": -1,
                            "MeasurementMatchesRemaining": 10,
                            "Tier": "",
                            "TierStart": 0,
                            "SubTier": 0,
                            "NextTier": "",
                            "NextTierStart": 0,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                        "AllTimeMax": {
                            "Value": -1,
                            "MeasurementMatchesRemaining": 10,
                            "Tier": "",
                            "TierStart": 0,
                            "SubTier": 0,
                            "NextTier": "",
                            "NextTierStart": 0,
                            "NextSubTier": 0,
                            "InitialMeasurementMatches": 10,
                        },
                    },
                },
                {
                    "Id": "xuid(2533274870001169)",
                    "ResultCode": 0,
                    "Result": {
                        "Current": {
                            "Value": 1513,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Onyx",
                            "TierStart": 1500,
                            "SubTier": 0,
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
                },
                {
                    "Id": "xuid(2533274840205695)",
                    "ResultCode": 0,
                    "Result": {
                        "Current": {
                            "Value": 1319,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Diamond",
                            "TierStart": 1300,
                            "SubTier": 2,
                            "NextTier": "Diamond",
                            "NextTierStart": 1350,
                            "NextSubTier": 3,
                            "InitialMeasurementMatches": 10,
                        },
                        "SeasonMax": {
                            "Value": 1401,
                            "MeasurementMatchesRemaining": 0,
                            "Tier": "Diamond",
                            "TierStart": 1400,
                            "SubTier": 4,
                            "NextTier": "Diamond",
                            "NextTierStart": 1450,
                            "NextSubTier": 5,
                            "InitialMeasurementMatches": 10,
                        },
                        "AllTimeMax": {
                            "Value": 1514,
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
                },
            ]
        }

        csr_data = csr(
            [2535405290989773, 2533274870001169, 2533274840205695], "test_playlist_id"
        )
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://skill.svc.halowaypoint.com:443/hi/playlist/test_playlist_id/csrs"
            "?players=xuid(2535405290989773),xuid(2533274870001169),xuid(2533274840205695)",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
                "343-clearance": self.clearance_token.flight_configuration_id,
            },
        )
        self.assertIn("2535405290989773", csr_data.get("Value")[0].get("Id"))
        self.assertIn("2533274870001169", csr_data.get("Value")[1].get("Id"))
        self.assertIn("2533274840205695", csr_data.get("Value")[2].get("Id"))
        mock_Session.reset_mock()

        # Failed call returns empty values
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({"Value": []}, csr([2533274870001169], "test_playlist_id"))
        self.assertDictEqual(
            {"Value": []},
            csr(
                [2535405290989773, 2533274870001169, 2533274840205695],
                "test_playlist_id",
            ),
        )

    @patch("apps.halo_infinite.api.match.requests.Session")
    def test_match_count(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "CustomMatchesPlayedCount": 1155,
            "MatchesPlayedCount": 4717,
            "MatchmadeMatchesPlayedCount": 3518,
            "LocalMatchesPlayedCount": 44,
        }
        match_count_data = match_count(2535405290989773)
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matches/count",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("CustomMatchesPlayedCount", match_count_data)
        self.assertIn("MatchesPlayedCount", match_count_data)
        self.assertIn("MatchmadeMatchesPlayedCount", match_count_data)
        self.assertIn("LocalMatchesPlayedCount", match_count_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, match_count(2535405290989773))

    @patch("apps.halo_infinite.api.match.requests.Session")
    def test_match_privacy(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "MatchmadeGames": 1,
            "OtherGames": 2,
        }
        match_privacy_data = match_privacy(2535405290989773)
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matches-privacy",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("MatchmadeGames", match_privacy_data)
        self.assertIn("OtherGames", match_privacy_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, match_privacy(2535405290989773))

    @patch("apps.halo_infinite.api.playlist.requests.Session")
    def test_playlist_info(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "NameHint": "solo-duo_ranked_keyboard_and_mouse",
            "PlatformMatchmakingHopperId": "GA-RETAIL_solo-duo_ranked_keyboard_and_mouse",
            "UgcPlaylistVersion": "c521cb83-5375-4cd8-992f-4f68765836fc",
            "GameStartRulesId": "rankedArenaSoloDuoMouseKeyboard",
            "TrueMatchSettings": "rankedPlayLoose.json",
            "ThunderheadContentConfiguration": "NonCampaign",
            "ThunderheadVmSize": "Medium",
            "HasCsr": True,
            "PlaylistExperience": "Arena",
            "MatchmakingDelaySec": 0,
        }
        playlist_info_data = playlist_info("test_playlist_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://gamecms-hacs.svc.halowaypoint.com/hi/multiplayer/file/playlists/assets/test_playlist_id.json",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("NameHint", playlist_info_data)
        self.assertIn("PlatformMatchmakingHopperId", playlist_info_data)
        self.assertIn("UgcPlaylistVersion", playlist_info_data)
        self.assertIn("GameStartRulesId", playlist_info_data)
        self.assertIn("TrueMatchSettings", playlist_info_data)
        self.assertIn("ThunderheadContentConfiguration", playlist_info_data)
        self.assertIn("ThunderheadVmSize", playlist_info_data)
        self.assertIn("HasCsr", playlist_info_data)
        self.assertIn("PlaylistExperience", playlist_info_data)
        self.assertIn("MatchmakingDelaySec", playlist_info_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, playlist_info("test_playlist_id"))

    @patch("apps.halo_infinite.api.playlist.requests.Session")
    def test_playlist_version(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "AssetId": "edfef3ac-9cbe-4fa2-b949-8f29deafd483",
            "VersionId": "61510620-3b02-439c-b9a1-39ac0e13797a",
            "PublicName": "Ranked Arena",
            "Description": "Competitive Halo Infinite Settings: Battle Rifle Starts. No Radar. "
            "Face off against other Spartans to earn or progress your rank.",
        }
        playlist_version_data = playlist_version("test_playlist_id", "test_version_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://discovery-infiniteugc.svc.halowaypoint.com:443/hi/playlists/test_playlist_id/"
            "versions/test_version_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("AssetId", playlist_version_data)
        self.assertIn("VersionId", playlist_version_data)
        self.assertIn("PublicName", playlist_version_data)
        self.assertIn("Description", playlist_version_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual(
            {}, playlist_version("test_playlist_id", "test_version_id")
        )

    @patch("apps.halo_infinite.api.service_record.requests.Session")
    def test_service_record(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "MatchesCompleted": 3518,
            "Wins": 1954,
            "Losses": 1496,
            "Ties": 57,
            "CoreStats": {
                "Kills": 47626,
                "Deaths": 37802,
                "Assists": 18549,
                "AverageKDA": 4.5500284252416145,
            },
        }
        service_record_data = service_record(2535405290989773)
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matchmade/servicerecord",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("MatchesCompleted", service_record_data)
        self.assertIn("Wins", service_record_data)
        self.assertIn("Losses", service_record_data)
        self.assertIn("Ties", service_record_data)
        self.assertIn("CoreStats", service_record_data)
        self.assertIn("Kills", service_record_data.get("CoreStats"))
        self.assertIn("Deaths", service_record_data.get("CoreStats"))
        self.assertIn("Assists", service_record_data.get("CoreStats"))
        self.assertIn("AverageKDA", service_record_data.get("CoreStats"))
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, service_record(2535405290989773))
