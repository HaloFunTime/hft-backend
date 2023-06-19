import datetime
from unittest.mock import call, patch

from django.contrib.auth.models import User
from django.test import TestCase

from apps.halo_infinite.api.csr import csr
from apps.halo_infinite.api.files import get_map, get_mode, get_prefab
from apps.halo_infinite.api.match import (
    match_count,
    match_privacy,
    match_skill,
    match_stats,
    matches_between,
)
from apps.halo_infinite.api.playlist import playlist_info, playlist_version
from apps.halo_infinite.api.recommended import recommended
from apps.halo_infinite.api.search import search_by_author
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

    @patch("apps.halo_infinite.api.files.requests.Session")
    def test_get_map(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": "test_id",
            "VersionId": "test_version_id",
            "PublicName": "Test Map",
            "Description": "This is a test description for Test Map.",
            "Files": {
                "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/test_id/test_version_id/",
                "FileRelativePaths": ["images/thumbnail.jpg"],
            },
            "Contributors": ["xuid(123)", "xuid(456)"],
            "AssetStats": {
                "PlaysRecent": 1,
                "PlaysAllTime": 2,
                "Favorites": 3,
                "AverageRating": 4,
                "NumberOfRatings": 5,
            },
            "PublishedDate": {"ISO8601Date": "2023-06-19T00:00:00.000Z"},
            "VersionNumber": 1234,
            "Admin": "xuid(123)",
        }
        get_map_data = get_map("test_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://discovery-infiniteugc.svc.halowaypoint.com/hi/maps/test_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("CustomData", get_map_data)
        self.assertIn("Tags", get_map_data)
        self.assertIn("AssetId", get_map_data)
        self.assertIn("VersionId", get_map_data)
        self.assertIn("PublicName", get_map_data)
        self.assertIn("Description", get_map_data)
        self.assertIn("Files", get_map_data)
        self.assertIn("Prefix", get_map_data.get("Files"))
        self.assertIn("FileRelativePaths", get_map_data.get("Files"))
        self.assertIn("Contributors", get_map_data)
        self.assertIn("AssetStats", get_map_data)
        self.assertIn("PlaysRecent", get_map_data.get("AssetStats"))
        self.assertIn("PlaysAllTime", get_map_data.get("AssetStats"))
        self.assertIn("Favorites", get_map_data.get("AssetStats"))
        self.assertIn("AverageRating", get_map_data.get("AssetStats"))
        self.assertIn("NumberOfRatings", get_map_data.get("AssetStats"))
        self.assertIn("PublishedDate", get_map_data)
        self.assertIn("VersionNumber", get_map_data)
        self.assertIn("Admin", get_map_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, get_map("test_id"))

    @patch("apps.halo_infinite.api.files.requests.Session")
    def test_get_mode(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": "test_id",
            "VersionId": "test_version_id",
            "PublicName": "Test Mode",
            "Description": "This is a test description for Test Mode.",
            "Files": {
                "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/ugcgamevariant/test_id/test_version_id/",  # noqa
                "FileRelativePaths": ["images/thumbnail.png"],
            },
            "Contributors": [],
            "AssetStats": {
                "PlaysRecent": 1,
                "PlaysAllTime": 2,
                "Favorites": 3,
                "AverageRating": 4,
                "NumberOfRatings": 5,
            },
            "PublishedDate": {"ISO8601Date": "2023-06-19T00:00:00.000Z"},
            "VersionNumber": 1234,
            "Admin": "xuid(123)",
        }
        get_mode_data = get_mode("test_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://discovery-infiniteugc.svc.halowaypoint.com/hi/ugcGameVariants/test_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("CustomData", get_mode_data)
        self.assertIn("Tags", get_mode_data)
        self.assertIn("AssetId", get_mode_data)
        self.assertIn("VersionId", get_mode_data)
        self.assertIn("PublicName", get_mode_data)
        self.assertIn("Description", get_mode_data)
        self.assertIn("Files", get_mode_data)
        self.assertIn("Prefix", get_mode_data.get("Files"))
        self.assertIn("FileRelativePaths", get_mode_data.get("Files"))
        self.assertIn("Contributors", get_mode_data)
        self.assertIn("AssetStats", get_mode_data)
        self.assertIn("PlaysRecent", get_mode_data.get("AssetStats"))
        self.assertIn("PlaysAllTime", get_mode_data.get("AssetStats"))
        self.assertIn("Favorites", get_mode_data.get("AssetStats"))
        self.assertIn("AverageRating", get_mode_data.get("AssetStats"))
        self.assertIn("NumberOfRatings", get_mode_data.get("AssetStats"))
        self.assertIn("PublishedDate", get_mode_data)
        self.assertIn("VersionNumber", get_mode_data)
        self.assertIn("Admin", get_mode_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, get_mode("test_id"))

    @patch("apps.halo_infinite.api.files.requests.Session")
    def test_get_prefab(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": "test_id",
            "VersionId": "test_version_id",
            "PublicName": "Test Prefab",
            "Description": "This is a test description for Test Prefab.",
            "Files": {
                "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/prefab/test_id/test_version_id/",
                "FileRelativePaths": ["images/thumbnail.jpg", "prefab.mvar"],
            },
            "Contributors": ["xuid(123)", "xuid(456)"],
            "AssetStats": {
                "PlaysRecent": 1,
                "PlaysAllTime": 2,
                "Favorites": 3,
                "AverageRating": 4,
                "NumberOfRatings": 5,
            },
            "PublishedDate": {"ISO8601Date": "2023-06-19T00:00:00.000Z"},
            "VersionNumber": 1234,
            "Admin": "xuid(123)",
        }
        get_prefab_data = get_prefab("test_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://discovery-infiniteugc.svc.halowaypoint.com/hi/prefabs/test_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("CustomData", get_prefab_data)
        self.assertIn("Tags", get_prefab_data)
        self.assertIn("AssetId", get_prefab_data)
        self.assertIn("VersionId", get_prefab_data)
        self.assertIn("PublicName", get_prefab_data)
        self.assertIn("Description", get_prefab_data)
        self.assertIn("Files", get_prefab_data)
        self.assertIn("Prefix", get_prefab_data.get("Files"))
        self.assertIn("FileRelativePaths", get_prefab_data.get("Files"))
        self.assertIn("Contributors", get_prefab_data)
        self.assertIn("AssetStats", get_prefab_data)
        self.assertIn("PlaysRecent", get_prefab_data.get("AssetStats"))
        self.assertIn("PlaysAllTime", get_prefab_data.get("AssetStats"))
        self.assertIn("Favorites", get_prefab_data.get("AssetStats"))
        self.assertIn("AverageRating", get_prefab_data.get("AssetStats"))
        self.assertIn("NumberOfRatings", get_prefab_data.get("AssetStats"))
        self.assertIn("PublishedDate", get_prefab_data)
        self.assertIn("VersionNumber", get_prefab_data)
        self.assertIn("Admin", get_prefab_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, get_prefab("test_id"))

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

    @patch("apps.halo_infinite.api.match.requests.Session")
    def test_match_skill(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "Value": [
                {
                    "Id": "xuid(2535405290989773)",
                    "Result": {
                        "RankRecap": {
                            "PreMatchCsr": {},
                            "PostMatchCsr": {},
                        },
                    },
                }
            ]
        }
        match_skill_data = match_skill(2535405290989773, "test_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://skill.svc.halowaypoint.com/hi/matches/test_id/skill?players=xuid(2535405290989773)",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("Value", match_skill_data)
        value = match_skill_data.get("Value")[0]
        self.assertIn("Id", value)
        self.assertIn("Result", value)
        rank_recap = value.get("Result").get("RankRecap")
        self.assertIn("PreMatchCsr", rank_recap)
        self.assertIn("PostMatchCsr", rank_recap)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, match_skill(2535405290989773, "test_id"))

    @patch("apps.halo_infinite.api.match.requests.Session")
    def test_match_stats(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "Value": [
                {
                    "Id": "xuid(2535405290989773)",
                    "Result": {
                        "RankRecap": {
                            "PreMatchCsr": {},
                            "PostMatchCsr": {},
                        },
                    },
                }
            ]
        }
        match_stats_data = match_stats("test_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/matches/test_id/stats",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("Value", match_stats_data)
        value = match_stats_data.get("Value")[0]
        self.assertIn("Id", value)
        self.assertIn("Result", value)
        rank_recap = value.get("Result").get("RankRecap")
        self.assertIn("PreMatchCsr", rank_recap)
        self.assertIn("PostMatchCsr", rank_recap)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, match_stats("test_id"))

    @patch("apps.halo_infinite.api.match.requests.Session")
    def test_matches_between(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "Start": 0,
            "Count": 25,
            "ResultCount": 25,
            "Results": [
                {
                    "MatchId": "test1",
                    "MatchInfo": {
                        "StartTime": "2023-01-02T07:50:24.936Z",
                        "EndTime": "2023-01-02T08:06:04.702Z",
                        "Duration": "PT15M18.2160311S",
                        "MapVariant": {},
                        "UgcGameVariant": {},
                        "Playlist": {},
                    },
                    "Outcome": 2,
                    "Rank": 1,
                    "PresentAtEndOfMatch": True,
                },
                {
                    "MatchId": "test2",
                    "MatchInfo": {
                        "StartTime": "2023-01-01T20:30:35.9Z",
                        "EndTime": "2023-01-01T20:46:14.302Z",
                        "Duration": "PT15M18.2009991S",
                        "MapVariant": {},
                        "UgcGameVariant": {},
                        "Playlist": {},
                    },
                    "Outcome": 2,
                    "Rank": 1,
                    "PresentAtEndOfMatch": True,
                },
                {
                    "MatchId": "test3",
                    "MatchInfo": {
                        "StartTime": "2022-12-30T05:09:18.875Z",
                        "EndTime": "2022-12-30T05:18:30.758Z",
                        "Duration": "PT8M37.3625903S",
                        "MapVariant": {},
                        "UgcGameVariant": {},
                        "Playlist": {},
                    },
                    "Outcome": 3,
                    "Rank": 12,
                    "PresentAtEndOfMatch": True,
                },
                {
                    "MatchId": "test4",
                    "MatchInfo": {
                        "StartTime": "2022-12-30T05:01:15.609Z",
                        "EndTime": "2022-12-30T05:07:50.548Z",
                        "Duration": "PT6M2.8487807S",
                        "MapVariant": {},
                        "UgcGameVariant": {},
                        "Playlist": {},
                    },
                    "Outcome": 3,
                    "Rank": 7,
                    "PresentAtEndOfMatch": True,
                },
                {
                    "MatchId": "90bd95ab-ea56-4f85-96ca-3c1aafc85cf1",
                    "MatchInfo": {
                        "StartTime": "2022-11-30T04:47:20.552Z",
                        "EndTime": "2022-11-30T04:59:32.674Z",
                        "Duration": "PT11M40.0166266S",
                        "MapVariant": {},
                        "UgcGameVariant": {},
                        "Playlist": {},
                    },
                    "Outcome": 3,
                    "Rank": 8,
                    "PresentAtEndOfMatch": True,
                },
            ],
        }
        matches_between_data = matches_between(
            2535405290989773,
            datetime.datetime(
                year=2022, month=12, day=30, tzinfo=datetime.timezone.utc
            ),
            datetime.datetime(year=2023, month=1, day=2, tzinfo=datetime.timezone.utc),
            "Matchmaking",
        )
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matches"
            "?count=25&start=0&type=Matchmaking",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertEqual(3, len(matches_between_data))
        for match_data in matches_between_data:
            self.assertIn("MatchId", match_data)
            self.assertIn("MatchInfo", match_data)
            match_info = match_data.get("MatchInfo")
            self.assertIn("StartTime", match_info)
            self.assertIn("EndTime", match_info)
            self.assertIn("Duration", match_info)
            self.assertIn("MapVariant", match_info)
            self.assertIn("UgcGameVariant", match_info)
            self.assertIn("Playlist", match_info)
            self.assertIn("Outcome", match_data)
            self.assertIn("Rank", match_data)
            self.assertIn("PresentAtEndOfMatch", match_data)
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertEqual(
            [],
            matches_between(
                2535405290989773,
                datetime.datetime(
                    year=2022, month=12, day=30, tzinfo=datetime.timezone.utc
                ),
                datetime.datetime(
                    year=2023, month=1, day=2, tzinfo=datetime.timezone.utc
                ),
                "Matchmaking",
            ),
        )

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

    @patch("apps.halo_infinite.api.recommended.requests.Session")
    def test_recommended(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "CustomData": {},
            "MapLinks": [
                {
                    "AssetId": "f633db01-3989-41d1-b6d4-bf2d220fc619",
                    "VersionId": "9b3ac4e6-d248-4122-adc5-a6d6697a19d1",
                    "PublicName": "Salvation",
                    "Description": "Those who are condemned, come here seeking salvation.",
                    "Files": {
                        "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/f633db01-3989-41d1-b6d4-bf2d220fc619/9b3ac4e6-d248-4122-adc5-a6d6697a19d1/",  # noqa
                        "FileRelativePaths": [
                            "images/hero.jpg",
                            "images/screenshot1.jpg",
                            "images/screenshot2.jpg",
                            "images/screenshot3.jpg",
                            "images/thumbnail.jpg",
                        ],
                        "PrefixEndpoint": {
                            "AuthorityId": "iUgcFiles",
                            "Path": "/ugcstorage/map/f633db01-3989-41d1-b6d4-bf2d220fc619/9b3ac4e6-d248-4122-adc5-a6d6697a19d1/",  # noqa
                            "QueryString": None,
                            "RetryPolicyId": "linearretry",
                            "TopicName": "",
                            "AcknowledgementTypeId": 0,
                            "AuthenticationLifetimeExtensionSupported": False,
                            "ClearanceAware": False,
                        },
                    },
                    "Contributors": [
                        "xuid(2814660312652330)",
                        "xuid(2533274795021402)",
                        "xuid(2535425050848538)",
                        "xuid(2533274801987300)",
                        "xuid(2533274835876334)",
                        "xuid(2535406614685708)",
                    ],
                    "AssetHome": 1,
                    "AssetStats": {
                        "PlaysRecent": 8561,
                        "PlaysAllTime": 87238,
                        "Favorites": 363,
                        "Likes": 0,
                        "Bookmarks": 0,
                        "ParentAssetCount": 4,
                        "AverageRating": 4.466666666666667,
                        "NumberOfRatings": 15,
                    },
                    "InspectionResult": 0,
                    "CloneBehavior": 0,
                    "Order": 2,
                    "PublishedDate": None,
                    "VersionNumber": 1,
                    "Admin": "xuid(2535406614685708)",
                },
                {
                    "AssetId": "74e1d570-f7a6-4f37-a68e-a0a51ab5bc3d",
                    "VersionId": "14fc528f-fbd7-4296-9bbd-00c68ca33177",
                    "PublicName": "Absolution",
                    "Description": "Imitation is the sincerest form of flattery.",
                    "Files": {
                        "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/74e1d570-f7a6-4f37-a68e-a0a51ab5bc3d/14fc528f-fbd7-4296-9bbd-00c68ca33177/",  # noqa
                        "FileRelativePaths": [
                            "images/hero.jpg",
                            "images/screenshot1.jpg",
                            "images/thumbnail.jpg",
                        ],
                        "PrefixEndpoint": {
                            "AuthorityId": "iUgcFiles",
                            "Path": "/ugcstorage/map/74e1d570-f7a6-4f37-a68e-a0a51ab5bc3d/14fc528f-fbd7-4296-9bbd-00c68ca33177/",  # noqa
                            "QueryString": None,
                            "RetryPolicyId": "linearretry",
                            "TopicName": "",
                            "AcknowledgementTypeId": 0,
                            "AuthenticationLifetimeExtensionSupported": False,
                            "ClearanceAware": False,
                        },
                    },
                    "Contributors": [
                        "xuid(2533274873806365)",
                        "xuid(2533274906188134)",
                        "xuid(2533274831077797)",
                        "xuid(2535406614685708)",
                    ],
                    "AssetHome": 1,
                    "AssetStats": {
                        "PlaysRecent": 8547,
                        "PlaysAllTime": 86947,
                        "Favorites": 330,
                        "Likes": 0,
                        "Bookmarks": 0,
                        "ParentAssetCount": 4,
                        "AverageRating": 4,
                        "NumberOfRatings": 14,
                    },
                    "InspectionResult": 0,
                    "CloneBehavior": 0,
                    "Order": 2,
                    "PublishedDate": None,
                    "VersionNumber": 1,
                    "Admin": "xuid(2535406614685708)",
                },
                {
                    "AssetId": "50771a22-62a7-4f1f-8982-3403857ba225",
                    "VersionId": "88da3483-83a3-4b0c-909b-9125f4602141",
                    "PublicName": "Starboard",
                    "Description": "General quarters, general quarters. All hands man your battle stations.",
                    "Files": {
                        "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/50771a22-62a7-4f1f-8982-3403857ba225/88da3483-83a3-4b0c-909b-9125f4602141/",  # noqa
                        "FileRelativePaths": [
                            "images/hero.jpg",
                            "images/screenshot1.jpg",
                            "images/screenshot2.jpg",
                            "images/screenshot3.jpg",
                            "images/thumbnail.jpg",
                        ],
                        "PrefixEndpoint": {
                            "AuthorityId": "iUgcFiles",
                            "Path": "/ugcstorage/map/50771a22-62a7-4f1f-8982-3403857ba225/88da3483-83a3-4b0c-909b-9125f4602141/",  # noqa
                            "QueryString": None,
                            "RetryPolicyId": "linearretry",
                            "TopicName": "",
                            "AcknowledgementTypeId": 0,
                            "AuthenticationLifetimeExtensionSupported": False,
                            "ClearanceAware": False,
                        },
                    },
                    "Contributors": [
                        "xuid(2535419870450908)",
                        "xuid(2533274968441932)",
                        "xuid(2535472198826651)",
                        "xuid(2533274876991706)",
                        "xuid(2535427784773192)",
                        "xuid(2533274825961918)",
                        "xuid(2535406614685708)",
                    ],
                    "AssetHome": 1,
                    "AssetStats": {
                        "PlaysRecent": 8667,
                        "PlaysAllTime": 87005,
                        "Favorites": 397,
                        "Likes": 0,
                        "Bookmarks": 0,
                        "ParentAssetCount": 4,
                        "AverageRating": 3.8260869565217392,
                        "NumberOfRatings": 23,
                    },
                    "InspectionResult": 0,
                    "CloneBehavior": 0,
                    "Order": 2,
                    "PublishedDate": None,
                    "VersionNumber": 1,
                    "Admin": "xuid(2535406614685708)",
                },
                {
                    "AssetId": "84254700-4df7-4677-904f-95d5ec391a8c",
                    "VersionId": "3bb86680-90f8-4f6e-a831-7fee38b77afd",
                    "PublicName": "Perilous",
                    "Description": "There's something in the water...",
                    "Files": {
                        "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/84254700-4df7-4677-904f-95d5ec391a8c/3bb86680-90f8-4f6e-a831-7fee38b77afd/",  # noqa
                        "FileRelativePaths": [
                            "images/hero.jpg",
                            "images/screenshot1.jpg",
                            "images/screenshot2.jpg",
                            "images/screenshot3.jpg",
                            "images/thumbnail.jpg",
                            "images/thumbnail.png",
                        ],
                        "PrefixEndpoint": {
                            "AuthorityId": "iUgcFiles",
                            "Path": "/ugcstorage/map/84254700-4df7-4677-904f-95d5ec391a8c/3bb86680-90f8-4f6e-a831-7fee38b77afd/",  # noqa
                            "QueryString": None,
                            "RetryPolicyId": "linearretry",
                            "TopicName": "",
                            "AcknowledgementTypeId": 0,
                            "AuthenticationLifetimeExtensionSupported": False,
                            "ClearanceAware": False,
                        },
                    },
                    "Contributors": [
                        "xuid(2599622463478870)",
                        "xuid(2533274839415478)",
                        "xuid(2535417458493667)",
                        "xuid(2533274835876334)",
                        "xuid(2533274807200960)",
                        "xuid(2535406614685708)",
                    ],
                    "AssetHome": 1,
                    "AssetStats": {
                        "PlaysRecent": 8550,
                        "PlaysAllTime": 86898,
                        "Favorites": 391,
                        "Likes": 0,
                        "Bookmarks": 0,
                        "ParentAssetCount": 4,
                        "AverageRating": 3.7857142857142856,
                        "NumberOfRatings": 28,
                    },
                    "InspectionResult": 0,
                    "CloneBehavior": 0,
                    "Order": 2,
                    "PublishedDate": None,
                    "VersionNumber": 1,
                    "Admin": "xuid(2535406614685708)",
                },
            ],
            "PlaylistLinks": [],
            "PrefabLinks": [],
            "UgcGameVariantLinks": [],
            "MapModePairLinks": [],
            "Tags": [],
            "AssetId": "712add52-f989-48e1-b3bb-ac7cd8a1c17a",
            "VersionId": "f4f63d62-9159-47f4-9fe6-1e976837f880",
            "PublicName": "343 Recommended",
            "Description": "A few things you might enjoy.",
            "Files": {
                "Prefix": "https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/project/712add52-f989-48e1-b3bb-ac7cd8a1c17a/f4f63d62-9159-47f4-9fe6-1e976837f880/",  # noqa
                "FileRelativePaths": [],
                "PrefixEndpoint": {
                    "AuthorityId": "iUgcFiles",
                    "Path": "/ugcstorage/project/712add52-f989-48e1-b3bb-ac7cd8a1c17a/f4f63d62-9159-47f4-9fe6-1e976837f880/",  # noqa
                    "QueryString": None,
                    "RetryPolicyId": "linearretry",
                    "TopicName": "",
                    "AcknowledgementTypeId": 0,
                    "AuthenticationLifetimeExtensionSupported": False,
                    "ClearanceAware": False,
                },
            },
            "Contributors": ["aaid(5c7909e9-3620-4920-8abf-f18cfb4333b6)"],
            "AssetHome": 1,
            "AssetStats": {
                "PlaysRecent": 0,
                "PlaysAllTime": 0,
                "Favorites": 0,
                "Likes": 0,
                "Bookmarks": 0,
                "ParentAssetCount": 0,
                "AverageRating": 0,
                "NumberOfRatings": 0,
            },
            "InspectionResult": 0,
            "CloneBehavior": 0,
            "Order": 0,
            "PublishedDate": {"ISO8601Date": "2023-02-28T18:01:08.419Z"},
            "VersionNumber": 47,
            "Admin": "aaid(5c7909e9-3620-4920-8abf-f18cfb4333b6)",
        }
        recommended_data = recommended()
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://discovery-infiniteugc.svc.halowaypoint.com:443/hi/projects/712add52-f989-48e1-b3bb-ac7cd8a1c17a",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertIn("CustomData", recommended_data)
        self.assertIn("MapLinks", recommended_data)
        self.assertIn("PlaylistLinks", recommended_data)
        self.assertIn("PrefabLinks", recommended_data)
        self.assertIn("UgcGameVariantLinks", recommended_data)
        self.assertIn("MapModePairLinks", recommended_data)
        self.assertIn("AssetId", recommended_data)
        self.assertIn("VersionId", recommended_data)
        self.assertIn("PublicName", recommended_data)
        self.assertIn("Description", recommended_data)
        self.assertIn("PublishedDate", recommended_data)
        self.assertIn("VersionNumber", recommended_data)
        map_links = recommended_data.get("MapLinks")
        self.assertEqual("Salvation", map_links[0].get("PublicName"))
        self.assertEqual("Absolution", map_links[1].get("PublicName"))
        self.assertEqual("Starboard", map_links[2].get("PublicName"))
        self.assertEqual("Perilous", map_links[3].get("PublicName"))
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, recommended())

    @patch("apps.halo_infinite.api.search.requests.Session")
    def test_search_by_author(self, mock_Session):
        # Successful call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.side_effect = [
            {
                "Tags": [],
                "EstimatedTotal": 9,
                "Start": 0,
                "Count": 5,
                "ResultCount": 5,
                "Results": [
                    {"AssetId": "test0"},
                    {"AssetId": "test1"},
                    {"AssetId": "test2"},
                    {"AssetId": "test3"},
                    {"AssetId": "test4"},
                ],
                "Links": {},
            },
            {
                "Tags": [],
                "EstimatedTotal": 9,
                "Start": 5,
                "Count": 5,
                "ResultCount": 4,
                "Results": [
                    {"AssetId": "test5"},
                    {"AssetId": "test6"},
                    {"AssetId": "test7"},
                    {"AssetId": "test8"},
                ],
                "Links": {},
            },
        ]
        search_by_author_data = search_by_author(2535405290989773, 5)
        self.assertEqual(
            mock_Session.return_value.__enter__.return_value.get.mock_calls[0],
            call(
                "https://discovery-infiniteugc.svc.halowaypoint.com/hi/search"
                "?author=xuid(2535405290989773)&count=5&start=0",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                    "x-343-authorization-spartan": self.spartan_token.token,
                },
            ),
        )
        self.assertEqual(
            mock_Session.return_value.__enter__.return_value.get.mock_calls[1],
            call().json(),
        )
        self.assertEqual(
            mock_Session.return_value.__enter__.return_value.get.mock_calls[2],
            call(
                "https://discovery-infiniteugc.svc.halowaypoint.com/hi/search"
                "?author=xuid(2535405290989773)&count=5&start=5",
                headers={
                    "Accept": "application/json",
                    "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                    "x-343-authorization-spartan": self.spartan_token.token,
                },
            ),
        )
        self.assertEqual(
            mock_Session.return_value.__enter__.return_value.get.mock_calls[3],
            call().json(),
        )
        self.assertEqual(len(search_by_author_data), 9)
        self.assertEqual(search_by_author_data[0], {"AssetId": "test0"})
        self.assertEqual(search_by_author_data[1], {"AssetId": "test1"})
        self.assertEqual(search_by_author_data[2], {"AssetId": "test2"})
        self.assertEqual(search_by_author_data[3], {"AssetId": "test3"})
        self.assertEqual(search_by_author_data[4], {"AssetId": "test4"})
        self.assertEqual(search_by_author_data[5], {"AssetId": "test5"})
        self.assertEqual(search_by_author_data[6], {"AssetId": "test6"})
        self.assertEqual(search_by_author_data[7], {"AssetId": "test7"})
        self.assertEqual(search_by_author_data[8], {"AssetId": "test8"})
        mock_Session.reset_mock()

        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertEqual([], search_by_author(2535405290989773, 5))

    @patch("apps.halo_infinite.api.service_record.requests.Session")
    def test_service_record(self, mock_Session):
        # Failed call
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            404
        )
        self.assertDictEqual({}, service_record(2535405290989773))
        mock_Session.reset_mock()

        # Successful call - all seasons
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
        self.assertEqual(service_record_data.get("MatchesCompleted"), 3518)
        self.assertEqual(service_record_data.get("Wins"), 1954)
        self.assertEqual(service_record_data.get("Losses"), 1496)
        self.assertEqual(service_record_data.get("Ties"), 57)
        self.assertIn("CoreStats", service_record_data)
        self.assertEqual(service_record_data.get("CoreStats").get("Kills"), 47626)
        self.assertEqual(service_record_data.get("CoreStats").get("Deaths"), 37802)
        self.assertEqual(service_record_data.get("CoreStats").get("Assists"), 18549)
        self.assertEqual(
            service_record_data.get("CoreStats").get("AverageKDA"), 4.5500284252416145
        )
        mock_Session.reset_mock()

        # Successful call - specific season
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "MatchesCompleted": 1759,
            "Wins": 977,
            "Losses": 748,
            "Ties": 34,
            "CoreStats": {
                "Kills": 4762,
                "Deaths": 3780,
                "Assists": 1854,
                "AverageKDA": 2.012345,
            },
        }
        service_record_data = service_record(2535405290989773, "test_season_id")
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matchmade/servicerecord"
            "?SeasonId=test_season_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertEqual(service_record_data.get("MatchesCompleted"), 1759)
        self.assertEqual(service_record_data.get("Wins"), 977)
        self.assertEqual(service_record_data.get("Losses"), 748)
        self.assertEqual(service_record_data.get("Ties"), 34)
        self.assertIn("CoreStats", service_record_data)
        self.assertEqual(service_record_data.get("CoreStats").get("Kills"), 4762)
        self.assertEqual(service_record_data.get("CoreStats").get("Deaths"), 3780)
        self.assertEqual(service_record_data.get("CoreStats").get("Assists"), 1854)
        self.assertEqual(
            service_record_data.get("CoreStats").get("AverageKDA"), 2.012345
        )
        mock_Session.reset_mock()

        # Successful call - season and playlist
        mock_Session.return_value.__enter__.return_value.get.return_value.status_code = (
            200
        )
        mock_Session.return_value.__enter__.return_value.get.return_value.json.return_value = {
            "MatchesCompleted": 10,
            "Wins": 5,
            "Losses": 4,
            "Ties": 1,
            "CoreStats": {
                "Kills": 123,
                "Deaths": 99,
                "Assists": 40,
                "AverageKDA": 1.111111111,
            },
        }
        service_record_data = service_record(
            2535405290989773, "test_season_id", "test_playlist_id"
        )
        mock_Session.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://halostats.svc.halowaypoint.com/hi/players/xuid(2535405290989773)/matchmade/servicerecord"
            "?SeasonId=test_season_id&PlaylistAssetId=test_playlist_id",
            headers={
                "Accept": "application/json",
                "User-Agent": "HaloWaypoint/2021112313511900 CFNetwork/1327.0.4 Darwin/21.2.0",
                "x-343-authorization-spartan": self.spartan_token.token,
            },
        )
        self.assertEqual(service_record_data.get("MatchesCompleted"), 10)
        self.assertEqual(service_record_data.get("Wins"), 5)
        self.assertEqual(service_record_data.get("Losses"), 4)
        self.assertEqual(service_record_data.get("Ties"), 1)
        self.assertIn("CoreStats", service_record_data)
        self.assertEqual(service_record_data.get("CoreStats").get("Kills"), 123)
        self.assertEqual(service_record_data.get("CoreStats").get("Deaths"), 99)
        self.assertEqual(service_record_data.get("CoreStats").get("Assists"), 40)
        self.assertEqual(
            service_record_data.get("CoreStats").get("AverageKDA"), 1.111111111
        )
        mock_Session.reset_mock()
