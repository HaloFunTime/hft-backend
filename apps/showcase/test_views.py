import uuid
from collections import OrderedDict
from unittest.mock import patch

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APIClient, APITestCase

from apps.showcase.models import ShowcaseFile


class ShowcaseTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    @patch("apps.showcase.views.get_prefab")
    @patch("apps.showcase.views.get_mode")
    @patch("apps.showcase.views.get_map")
    def test_check_showcase_view(self, mock_get_map, mock_get_mode, mock_get_prefab):
        # Missing field values throw errors
        response = self.client.post("/showcase/check-showcase", {}, format="json")
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

        # Improperly formatted values throw errors
        response = self.client.post(
            "/showcase/check-showcase",
            {
                "discordUserId": "abc",
                "discordUsername": "f",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        details = response.data.get("error").get("details")
        self.assertIn("discordUserId", details)
        self.assertEqual(
            details.get("discordUserId")[0],
            ErrorDetail(string="Only numeric characters are allowed.", code="invalid"),
        )
        self.assertIn("discordUsername", details)
        self.assertEqual(
            details.get("discordUsername")[0],
            ErrorDetail(
                string="Ensure this field has at least 2 characters.",
                code="min_length",
            ),
        )

        # No showcase data
        response = self.client.post(
            "/showcase/check-showcase",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(response.data.get("showcaseFiles"), [])

        # Showcase has one map, one mode, one prefab
        map_asset_id = uuid.uuid4()
        map_version_id = uuid.uuid4()
        mock_get_map.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": map_asset_id,
            "VersionId": map_version_id,
            "PublicName": "Test Map",
            "Description": "This is a test description for Test Map.",
            "Files": {
                "Prefix": f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/{map_asset_id}/{map_version_id}/",  # noqa
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
            "VersionNumber": 12,
            "Admin": "xuid(123)",
        }
        mode_asset_id = uuid.uuid4()
        mode_version_id = uuid.uuid4()
        mock_get_mode.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": mode_asset_id,
            "VersionId": mode_version_id,
            "PublicName": "Test Mode",
            "Description": "This is a test description for Test Mode.",
            "Files": {
                "Prefix": f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/ugcgamevariant/{mode_asset_id}/{mode_version_id}/",  # noqa
                "FileRelativePaths": ["images/thumbnail.png"],
            },
            "Contributors": [],
            "AssetStats": {
                "PlaysRecent": 5,
                "PlaysAllTime": 1,
                "Favorites": 2,
                "AverageRating": 3,
                "NumberOfRatings": 4,
            },
            "PublishedDate": {"ISO8601Date": "2023-06-19T00:00:00.000Z"},
            "VersionNumber": 123,
            "Admin": "xuid(123)",
        }
        prefab_asset_id = uuid.uuid4()
        prefab_version_id = uuid.uuid4()
        mock_get_prefab.return_value = {
            "CustomData": {},
            "Tags": [],
            "AssetId": prefab_asset_id,
            "VersionId": prefab_version_id,
            "PublicName": "Test Prefab",
            "Description": "This is a test description for Test Prefab.",
            "Files": {
                "Prefix": f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/prefab/{prefab_asset_id}/{prefab_version_id}/",  # noqa
                "FileRelativePaths": ["images/thumbnail.jpg", "prefab.mvar"],
            },
            "Contributors": ["xuid(123)", "xuid(456)"],
            "AssetStats": {
                "PlaysRecent": 4,
                "PlaysAllTime": 5,
                "Favorites": 1,
                "AverageRating": 2,
                "NumberOfRatings": 3,
            },
            "PublishedDate": {"ISO8601Date": "2023-06-19T00:00:00.000Z"},
            "VersionNumber": 1234,
            "Admin": "xuid(123)",
        }
        ShowcaseFile.objects.create(
            showcase_owner_id="123",
            file_id=map_asset_id,
            file_type=ShowcaseFile.FileType.Map,
            position=1,
            creator=self.user,
        )
        ShowcaseFile.objects.create(
            showcase_owner_id="123",
            file_id=mode_asset_id,
            file_type=ShowcaseFile.FileType.Mode,
            position=2,
            creator=self.user,
        )
        ShowcaseFile.objects.create(
            showcase_owner_id="123",
            file_id=prefab_asset_id,
            file_type=ShowcaseFile.FileType.Prefab,
            position=3,
            creator=self.user,
        )
        response = self.client.post(
            "/showcase/check-showcase",
            {
                "discordUserId": "123",
                "discordUsername": "test123",
            },
            format="json",
        )
        self.assertEqual(response.data.get("discordUserId"), "123")
        self.assertEqual(
            response.data.get("showcaseFiles"),
            [
                OrderedDict(
                    [
                        ("fileType", "map"),
                        ("name", "Test Map"),
                        ("description", "This is a test description for Test Map."),
                        (
                            "thumbnailURL",
                            f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/map/{map_asset_id}/{map_version_id}/images/thumbnail.jpg",  # noqa
                        ),
                        (
                            "waypointURL",
                            f"https://www.halowaypoint.com/halo-infinite/ugc/maps/{map_asset_id}",
                        ),
                        ("plays", 2),
                        ("favorites", 3),
                        ("ratings", 5),
                        ("averageRating", "4.000000000000000"),
                    ]
                ),
                OrderedDict(
                    [
                        ("fileType", "mode"),
                        ("name", "Test Mode"),
                        ("description", "This is a test description for Test Mode."),
                        (
                            "thumbnailURL",
                            f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/ugcgamevariant/{mode_asset_id}/{mode_version_id}/images/thumbnail.png",  # noqa
                        ),
                        (
                            "waypointURL",
                            f"https://www.halowaypoint.com/halo-infinite/ugc/modes/{mode_asset_id}",
                        ),
                        ("plays", 1),
                        ("favorites", 2),
                        ("ratings", 4),
                        ("averageRating", "3.000000000000000"),
                    ]
                ),
                OrderedDict(
                    [
                        ("fileType", "prefab"),
                        ("name", "Test Prefab"),
                        ("description", "This is a test description for Test Prefab."),
                        (
                            "thumbnailURL",
                            f"https://blobs-infiniteugc.svc.halowaypoint.com/ugcstorage/prefab/{prefab_asset_id}/{prefab_version_id}/images/thumbnail.jpg",  # noqa
                        ),
                        (
                            "waypointURL",
                            f"https://www.halowaypoint.com/halo-infinite/ugc/prefabs/{prefab_asset_id}",
                        ),
                        ("plays", 5),
                        ("favorites", 1),
                        ("ratings", 3),
                        ("averageRating", "2.000000000000000"),
                    ]
                ),
            ],
        )
        mock_get_map.assert_called_once_with(map_asset_id)
        mock_get_mode.assert_called_once_with(mode_asset_id)
        mock_get_prefab.assert_called_once_with(prefab_asset_id)

    # TODO: Write this test
    def test_add_file_view(self):
        pass

    # TODO: Write this test
    def test_remove_file_view(self):
        pass
