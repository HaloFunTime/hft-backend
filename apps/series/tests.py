import itertools
import json
import random
import uuid
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.series.exceptions import (
    SeriesBuildImpossibleException,
    SeriesBuildTimeoutException,
    SeriesBuildUnsupportedException,
)
from apps.series.models import SeriesGametype, SeriesMap, SeriesMode, SeriesRuleset
from apps.series.utils import build_best_of_dict, build_series


def ruleset_factory(creator: User, name: str = None) -> SeriesRuleset:
    test_uuid = uuid.uuid4().hex
    return SeriesRuleset.objects.create(
        creator=creator,
        name=test_uuid if name is None else name,
        id=test_uuid,
    )


def map_factory(creator: User, name: str = None) -> SeriesMap:
    return SeriesMap.objects.create(
        creator=creator, name=uuid.uuid4().hex if name is None else name
    )


def mode_factory(creator: User, name: str = None) -> SeriesMode:
    return SeriesMode.objects.create(
        creator=creator, name=uuid.uuid4().hex if name is None else name
    )


def gametype_factory(
    creator: User,
    ruleset: SeriesRuleset = None,
    map: SeriesMap = None,
    mode: SeriesMode = None,
) -> SeriesGametype:
    return SeriesGametype.objects.create(
        creator=creator,
        ruleset=ruleset_factory(creator, None) if ruleset is None else ruleset,
        map=map_factory(creator, None) if map is None else map,
        mode=mode_factory(creator, None) if mode is None else mode,
    )


class SeriesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, _created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_series_success(self):
        # Empty SeriesRuleset table returns empty array
        response = self.client.get("/series/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        # SeriesRuleset table with one entry returns it
        test_ruleset_1 = ruleset_factory(self.user, "test")
        response = self.client.get("/series/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data, [{"name": test_ruleset_1.name, "id": test_ruleset_1.id}]
        )

        # SeriesRuleset table with two entries returns both, ordered by name
        test_ruleset_2 = ruleset_factory(self.user, "another")
        response = self.client.get("/series/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [
                {"name": test_ruleset_2.name, "id": test_ruleset_2.id},
                {"name": test_ruleset_1.name, "id": test_ruleset_1.id},
            ],
        )

    @patch("apps.series.views.build_series")
    def test_bo3_success(self, mock_build_series):
        # Set up some test data: ruleset and 3 gametypes
        ruleset = ruleset_factory(self.user)
        gametypes = []
        for _ in range(3):
            gametypes.append(gametype_factory(self.user, ruleset))
        mock_build_series.return_value = gametypes

        response = self.client.get(f"/series/{ruleset.id}/bo3")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")
        self.assertEqual(
            json.loads(response.content),
            {
                "title": ruleset.name,
                "subtitle": "Best of 3",
                "game_1": {
                    "map": gametypes[0].map.name,
                    "map_file_id": gametypes[0].map.hi_asset_id
                    if gametypes[0].map.hi_asset_id
                    else None,
                    "mode": gametypes[0].mode.name,
                    "mode_file_id": gametypes[0].mode.hi_asset_id
                    if gametypes[0].mode.hi_asset_id
                    else None,
                },
                "game_2": {
                    "map": gametypes[1].map.name,
                    "map_file_id": gametypes[1].map.hi_asset_id
                    if gametypes[1].map.hi_asset_id
                    else None,
                    "mode": gametypes[1].mode.name,
                    "mode_file_id": gametypes[1].mode.hi_asset_id
                    if gametypes[1].mode.hi_asset_id
                    else None,
                },
                "game_3": {
                    "map": gametypes[2].map.name,
                    "map_file_id": gametypes[2].map.hi_asset_id
                    if gametypes[2].map.hi_asset_id
                    else None,
                    "mode": gametypes[2].mode.name,
                    "mode_file_id": gametypes[2].mode.hi_asset_id
                    if gametypes[2].mode.hi_asset_id
                    else None,
                },
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo5_success(self, mock_build_series):
        # Set up some test data: ruleset and 5 gametypes
        ruleset = ruleset_factory(self.user)
        gametypes = []
        for _ in range(5):
            gametypes.append(gametype_factory(self.user, ruleset))
        mock_build_series.return_value = gametypes

        response = self.client.get(f"/series/{ruleset.id}/bo5")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")
        self.assertEqual(
            json.loads(response.content),
            {
                "title": ruleset.name,
                "subtitle": "Best of 5",
                "game_1": {
                    "map": gametypes[0].map.name,
                    "map_file_id": gametypes[0].map.hi_asset_id
                    if gametypes[0].map.hi_asset_id
                    else None,
                    "mode": gametypes[0].mode.name,
                    "mode_file_id": gametypes[0].mode.hi_asset_id
                    if gametypes[0].mode.hi_asset_id
                    else None,
                },
                "game_2": {
                    "map": gametypes[1].map.name,
                    "map_file_id": gametypes[1].map.hi_asset_id
                    if gametypes[1].map.hi_asset_id
                    else None,
                    "mode": gametypes[1].mode.name,
                    "mode_file_id": gametypes[1].mode.hi_asset_id
                    if gametypes[1].mode.hi_asset_id
                    else None,
                },
                "game_3": {
                    "map": gametypes[2].map.name,
                    "map_file_id": gametypes[2].map.hi_asset_id
                    if gametypes[2].map.hi_asset_id
                    else None,
                    "mode": gametypes[2].mode.name,
                    "mode_file_id": gametypes[2].mode.hi_asset_id
                    if gametypes[2].mode.hi_asset_id
                    else None,
                },
                "game_4": {
                    "map": gametypes[3].map.name,
                    "map_file_id": gametypes[3].map.hi_asset_id
                    if gametypes[3].map.hi_asset_id
                    else None,
                    "mode": gametypes[3].mode.name,
                    "mode_file_id": gametypes[3].mode.hi_asset_id
                    if gametypes[3].mode.hi_asset_id
                    else None,
                },
                "game_5": {
                    "map": gametypes[4].map.name,
                    "map_file_id": gametypes[4].map.hi_asset_id
                    if gametypes[4].map.hi_asset_id
                    else None,
                    "mode": gametypes[4].mode.name,
                    "mode_file_id": gametypes[4].mode.hi_asset_id
                    if gametypes[4].mode.hi_asset_id
                    else None,
                },
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo7_success(self, mock_build_series):
        # Set up some test data: ruleset and 7 gametypes
        ruleset = ruleset_factory(self.user)
        gametypes = []
        for _ in range(7):
            gametypes.append(gametype_factory(self.user, ruleset))
        mock_build_series.return_value = gametypes

        response = self.client.get(f"/series/{ruleset.id}/bo7")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-cache")
        self.assertEqual(
            json.loads(response.content),
            {
                "title": ruleset.name,
                "subtitle": "Best of 7",
                "game_1": {
                    "map": gametypes[0].map.name,
                    "map_file_id": gametypes[0].map.hi_asset_id
                    if gametypes[0].map.hi_asset_id
                    else None,
                    "mode": gametypes[0].mode.name,
                    "mode_file_id": gametypes[0].mode.hi_asset_id
                    if gametypes[0].mode.hi_asset_id
                    else None,
                },
                "game_2": {
                    "map": gametypes[1].map.name,
                    "map_file_id": gametypes[1].map.hi_asset_id
                    if gametypes[1].map.hi_asset_id
                    else None,
                    "mode": gametypes[1].mode.name,
                    "mode_file_id": gametypes[1].mode.hi_asset_id
                    if gametypes[1].mode.hi_asset_id
                    else None,
                },
                "game_3": {
                    "map": gametypes[2].map.name,
                    "map_file_id": gametypes[2].map.hi_asset_id
                    if gametypes[2].map.hi_asset_id
                    else None,
                    "mode": gametypes[2].mode.name,
                    "mode_file_id": gametypes[2].mode.hi_asset_id
                    if gametypes[2].mode.hi_asset_id
                    else None,
                },
                "game_4": {
                    "map": gametypes[3].map.name,
                    "map_file_id": gametypes[3].map.hi_asset_id
                    if gametypes[3].map.hi_asset_id
                    else None,
                    "mode": gametypes[3].mode.name,
                    "mode_file_id": gametypes[3].mode.hi_asset_id
                    if gametypes[3].mode.hi_asset_id
                    else None,
                },
                "game_5": {
                    "map": gametypes[4].map.name,
                    "map_file_id": gametypes[4].map.hi_asset_id
                    if gametypes[4].map.hi_asset_id
                    else None,
                    "mode": gametypes[4].mode.name,
                    "mode_file_id": gametypes[4].mode.hi_asset_id
                    if gametypes[4].mode.hi_asset_id
                    else None,
                },
                "game_6": {
                    "map": gametypes[5].map.name,
                    "map_file_id": gametypes[5].map.hi_asset_id
                    if gametypes[5].map.hi_asset_id
                    else None,
                    "mode": gametypes[5].mode.name,
                    "mode_file_id": gametypes[5].mode.hi_asset_id
                    if gametypes[5].mode.hi_asset_id
                    else None,
                },
                "game_7": {
                    "map": gametypes[6].map.name,
                    "map_file_id": gametypes[6].map.hi_asset_id
                    if gametypes[6].map.hi_asset_id
                    else None,
                    "mode": gametypes[6].mode.name,
                    "mode_file_id": gametypes[6].mode.hi_asset_id
                    if gametypes[6].mode.hi_asset_id
                    else None,
                },
            },
        )

    def test_bestof_failures_missing_id(self):
        response = self.client.get("/series//bo3")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/series//bo5")
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/series//bo7")
        self.assertEqual(response.status_code, 404)

    def test_bestof_failures_404(self):
        response = self.client.get("/series/foo/bo3")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.data, {"error": "Could not retrieve 'foo' series ruleset."}
        )
        response = self.client.get("/series/foo/bo5")
        self.assertEqual(
            response.data, {"error": "Could not retrieve 'foo' series ruleset."}
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.get("/series/foo/bo7")
        self.assertEqual(
            response.data, {"error": "Could not retrieve 'foo' series ruleset."}
        )
        self.assertEqual(response.status_code, 404)

    @patch("apps.series.views.build_series")
    def test_bo3_failure_too_strict(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildImpossibleException
        response = self.client.get(f"/series/{ruleset.id}/bo3")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo5_failure_too_strict(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildImpossibleException
        response = self.client.get(f"/series/{ruleset.id}/bo5")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo7_failure_too_strict(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildImpossibleException
        response = self.client.get(f"/series/{ruleset.id}/bo7")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo3_failure_too_loose(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildTimeoutException
        response = self.client.get(f"/series/{ruleset.id}/bo3")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Remove some gametypes or tighten the ruleset restrictions."
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo5_failure_too_loose(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildTimeoutException
        response = self.client.get(f"/series/{ruleset.id}/bo5")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Remove some gametypes or tighten the ruleset restrictions."
            },
        )

    @patch("apps.series.views.build_series")
    def test_bo7_failure_too_loose(self, mock_build_series):
        # Set up some test data: ruleset
        ruleset = ruleset_factory(self.user)

        # Test build impossible
        mock_build_series.side_effect = SeriesBuildTimeoutException
        response = self.client.get(f"/series/{ruleset.id}/bo7")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.data,
            {
                "error": "Cannot build series. Remove some gametypes or tighten the ruleset restrictions."
            },
        )


class SeriesUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_build_series_validations(self):
        ruleset = ruleset_factory(self.user)

        # Series build is unsupported for numbers other than 3, 5, or 7
        for x in range(0, 100):
            if x == 3 or x == 5 or x == 7:
                continue
            self.assertRaisesMessage(
                SeriesBuildUnsupportedException,
                "Only 3, 5, and 7 game series may be built",
                build_series,
                ruleset,
                x,
            )

        # Series build is impossible if a ruleset has fewer gametypes than the prescribed length
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "Not enough gametypes to build series",
            build_series,
            ruleset,
            3,
        )
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "Not enough gametypes to build series",
            build_series,
            ruleset,
            5,
        )
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "Not enough gametypes to build series",
            build_series,
            ruleset,
            7,
        )

        # Series build is impossible if there are no combinations of gametypes matching the ruleset's restrictions
        # Bo3 impossible
        bo3_ruleset = ruleset_factory(self.user, "Bo3")
        bo3_ruleset.allow_bo3_map_repeats = False
        bo3_ruleset.save()
        bo3_map = map_factory(self.user)
        for _ in range(3):
            gametype_factory(self.user, bo3_ruleset, bo3_map)
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "No valid combinations to build series",
            build_series,
            bo3_ruleset,
            3,
        )
        # Bo5 impossible
        bo5_ruleset = ruleset_factory(self.user, "Bo5")
        bo5_ruleset.allow_bo5_map_repeats = False
        bo5_ruleset.save()
        bo5_map = map_factory(self.user)
        for _ in range(5):
            gametype_factory(self.user, bo5_ruleset, bo5_map)
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "No valid combinations to build series",
            build_series,
            bo5_ruleset,
            5,
        )
        # Bo7 impossible
        bo7_ruleset = ruleset_factory(self.user, "Bo7")
        bo7_ruleset.allow_bo7_map_repeats = False
        bo7_ruleset.save()
        bo7_map = map_factory(self.user)
        for _ in range(7):
            gametype_factory(self.user, bo7_ruleset, bo7_map)
        self.assertRaisesMessage(
            SeriesBuildImpossibleException,
            "No valid combinations to build series",
            build_series,
            bo7_ruleset,
            7,
        )

    def test_build_series_hcs(self):
        # Set up the HCS 2022 Split 2 Ruleset/Maps/Modes
        ruleset = ruleset_factory(self.user, "Halo Championship Series")
        maps_by_name = {}
        for name in [
            "Aquarius",
            "Bazaar",
            "Catalyst",
            "Live Fire",
            "Recharge",
            "Streets",
        ]:
            maps_by_name[name] = map_factory(self.user, name)
        modes_by_name = {}
        for name in [
            "Capture the Flag",
            "King of the Hill",
            "Oddball",
            "Slayer",
            "Strongholds",
        ]:
            modes_by_name[name] = mode_factory(self.user, name)
        ruleset.allow_bo7_map_repeats = True
        ruleset.featured_mode = modes_by_name["Slayer"]
        ruleset.save()
        # Set up the HCS 2022 Split 2 Gametypes
        gametype_tuples = [
            ("Capture the Flag", "Aquarius"),
            ("Capture the Flag", "Bazaar"),
            ("Capture the Flag", "Catalyst"),
            ("King of the Hill", "Live Fire"),
            ("King of the Hill", "Recharge"),
            ("King of the Hill", "Streets"),
            ("Oddball", "Live Fire"),
            ("Oddball", "Recharge"),
            ("Oddball", "Streets"),
            ("Slayer", "Aquarius"),
            ("Slayer", "Catalyst"),
            ("Slayer", "Live Fire"),
            ("Slayer", "Recharge"),
            ("Slayer", "Streets"),
            ("Strongholds", "Live Fire"),
            ("Strongholds", "Recharge"),
            ("Strongholds", "Streets"),
        ]
        gametypes = []
        for gametype_tuple in gametype_tuples:
            gametypes.append(
                gametype_factory(
                    self.user,
                    ruleset,
                    maps_by_name[gametype_tuple[1]],
                    modes_by_name[gametype_tuple[0]],
                )
            )

        # Bo3 Validations
        bo3_gametypes = build_series(ruleset, 3)
        self.assertEqual(len(bo3_gametypes), 3)  # Should return 3 SeriesGametypes
        self.assertNotEqual(
            bo3_gametypes[0].mode, modes_by_name["Slayer"]
        )  # Game 1 should NOT be Slayer
        self.assertEqual(
            bo3_gametypes[1].mode, modes_by_name["Slayer"]
        )  # Game 2 should be Slayer
        self.assertNotEqual(
            bo3_gametypes[2].mode, modes_by_name["Slayer"]
        )  # Game 3 should NOT be Slayer
        for bo3_gametype in bo3_gametypes:
            self.assertIn(
                bo3_gametype, gametypes
            )  # Only valid gametypes should be included
        for a, b in itertools.combinations(bo3_gametypes, 2):
            self.assertNotEqual(a, b)  # No gametype should be repeated
            self.assertNotEqual(a.map, b.map)  # No map should be repeated
            self.assertNotEqual(a.mode, b.mode)  # No mode should be repeated

        # Bo5 Validations
        bo5_gametypes = build_series(ruleset, 5)
        self.assertEqual(len(bo5_gametypes), 5)  # Should return 5 SeriesGametypes
        self.assertNotEqual(
            bo5_gametypes[0].mode, modes_by_name["Slayer"]
        )  # Game 1 should NOT be Slayer
        self.assertEqual(
            bo5_gametypes[1].mode, modes_by_name["Slayer"]
        )  # Game 2 should be Slayer
        self.assertNotEqual(
            bo5_gametypes[2].mode, modes_by_name["Slayer"]
        )  # Game 3 should NOT be Slayer
        self.assertNotEqual(
            bo5_gametypes[3].mode, modes_by_name["Slayer"]
        )  # Game 4 should NOT be Slayer
        self.assertEqual(
            bo5_gametypes[4].mode, modes_by_name["Slayer"]
        )  # Game 5 should be Slayer
        for bo5_gametype in bo5_gametypes:
            self.assertIn(
                bo5_gametype, gametypes
            )  # Only valid gametypes should be included
        for a, b in itertools.combinations(bo5_gametypes, 2):
            self.assertNotEqual(a, b)  # No gametype should be repeated
            self.assertNotEqual(a.map, b.map)  # No map should be repeated
            if a.mode.name != "Slayer" and b.mode.name != "Slayer":
                self.assertNotEqual(
                    a.mode, b.mode
                )  # No non-Slayer mode should be repeated

        # Bo7 Validations
        bo7_gametypes = build_series(ruleset, 7)
        self.assertEqual(len(bo7_gametypes), 7)  # Should return 7 SeriesGametypes
        self.assertNotEqual(
            bo7_gametypes[0].mode, modes_by_name["Slayer"]
        )  # Game 1 should NOT be Slayer
        self.assertEqual(
            bo7_gametypes[1].mode, modes_by_name["Slayer"]
        )  # Game 2 should be Slayer
        self.assertNotEqual(
            bo7_gametypes[2].mode, modes_by_name["Slayer"]
        )  # Game 3 should NOT be Slayer
        self.assertNotEqual(
            bo7_gametypes[3].mode, modes_by_name["Slayer"]
        )  # Game 4 should NOT be Slayer
        self.assertEqual(
            bo7_gametypes[4].mode, modes_by_name["Slayer"]
        )  # Game 5 should be Slayer
        self.assertNotEqual(
            bo7_gametypes[5].mode, modes_by_name["Slayer"]
        )  # Game 6 should NOT be Slayer
        self.assertEqual(
            bo7_gametypes[6].mode, modes_by_name["Slayer"]
        )  # Game 7 should be Slayer
        for bo7_gametype in bo7_gametypes:
            self.assertIn(
                bo7_gametype, gametypes
            )  # Only valid gametypes should be included
        for a, b in itertools.combinations(bo7_gametypes, 2):
            self.assertNotEqual(a, b)  # No gametype should be repeated
            if a.mode.name != "Slayer" and b.mode.name != "Slayer":
                self.assertNotEqual(
                    a.mode, b.mode
                )  # No non-Slayer mode should be repeated

    @patch("apps.series.utils.time.perf_counter")
    def test_build_series_timeout(self, mock_perf_counter):
        mock_perf_counter.side_effect = [0, 1.1]
        ruleset = ruleset_factory(self.user)
        for _ in range(3):
            gametype_factory(self.user, ruleset)

        # Series build should time out if over a second is spent evaluating combinations
        self.assertRaisesMessage(
            SeriesBuildTimeoutException,
            "Took longer than one second to process potential series combinations",
            build_series,
            ruleset,
            3,
        )

    def test_build_best_of_dict(self):
        ruleset = ruleset_factory(self.user, "test")
        maps = []
        modes = []
        for i in range(0, 3):
            maps.append(map_factory(self.user, f"Test Map {i}"))
            modes.append(mode_factory(self.user, f"Test Mode {i}"))
        gametypes = []
        for test_map in maps:
            for test_mode in modes:
                gametypes.append(
                    gametype_factory(self.user, ruleset, test_map, test_mode)
                )

        # Works for Bo3
        chosen_gametypes = random.sample(gametypes, 3)
        test_dict_1 = build_best_of_dict(ruleset, chosen_gametypes)
        self.assertEqual(test_dict_1.get("title"), ruleset.name)
        self.assertEqual(
            test_dict_1.get("subtitle"), f"Best of {len(chosen_gametypes)}"
        )
        self.assertEqual(
            test_dict_1.get("game_1").get("map"), chosen_gametypes[0].map.name
        )
        self.assertEqual(
            test_dict_1.get("game_1").get("mode"), chosen_gametypes[0].mode.name
        )
        self.assertEqual(
            test_dict_1.get("game_2").get("map"), chosen_gametypes[1].map.name
        )
        self.assertEqual(
            test_dict_1.get("game_2").get("mode"), chosen_gametypes[1].mode.name
        )
        self.assertEqual(
            test_dict_1.get("game_3").get("map"), chosen_gametypes[2].map.name
        )
        self.assertEqual(
            test_dict_1.get("game_3").get("mode"), chosen_gametypes[2].mode.name
        )

        # Works for Bo5
        chosen_gametypes = random.sample(gametypes, 5)
        test_dict_2 = build_best_of_dict(ruleset, chosen_gametypes)
        self.assertEqual(test_dict_2.get("title"), ruleset.name)
        self.assertEqual(
            test_dict_2.get("subtitle"), f"Best of {len(chosen_gametypes)}"
        )
        self.assertEqual(
            test_dict_2.get("game_1").get("map"), chosen_gametypes[0].map.name
        )
        self.assertEqual(
            test_dict_2.get("game_1").get("mode"), chosen_gametypes[0].mode.name
        )
        self.assertEqual(
            test_dict_2.get("game_2").get("map"), chosen_gametypes[1].map.name
        )
        self.assertEqual(
            test_dict_2.get("game_2").get("mode"), chosen_gametypes[1].mode.name
        )
        self.assertEqual(
            test_dict_2.get("game_3").get("map"), chosen_gametypes[2].map.name
        )
        self.assertEqual(
            test_dict_2.get("game_3").get("mode"), chosen_gametypes[2].mode.name
        )
        self.assertEqual(
            test_dict_2.get("game_4").get("map"), chosen_gametypes[3].map.name
        )
        self.assertEqual(
            test_dict_2.get("game_4").get("mode"), chosen_gametypes[3].mode.name
        )
        self.assertEqual(
            test_dict_2.get("game_5").get("map"), chosen_gametypes[4].map.name
        )
        self.assertEqual(
            test_dict_2.get("game_5").get("mode"), chosen_gametypes[4].mode.name
        )

        # Works for Bo7
        chosen_gametypes = random.sample(gametypes, 7)
        test_dict_3 = build_best_of_dict(ruleset, chosen_gametypes)
        self.assertEqual(test_dict_3.get("title"), ruleset.name)
        self.assertEqual(
            test_dict_3.get("subtitle"), f"Best of {len(chosen_gametypes)}"
        )
        self.assertEqual(
            test_dict_3.get("game_1").get("map"), chosen_gametypes[0].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_1").get("mode"), chosen_gametypes[0].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_2").get("map"), chosen_gametypes[1].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_2").get("mode"), chosen_gametypes[1].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_3").get("map"), chosen_gametypes[2].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_3").get("mode"), chosen_gametypes[2].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_4").get("map"), chosen_gametypes[3].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_4").get("mode"), chosen_gametypes[3].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_5").get("map"), chosen_gametypes[4].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_5").get("mode"), chosen_gametypes[4].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_6").get("map"), chosen_gametypes[5].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_6").get("mode"), chosen_gametypes[5].mode.name
        )
        self.assertEqual(
            test_dict_3.get("game_7").get("map"), chosen_gametypes[6].map.name
        )
        self.assertEqual(
            test_dict_3.get("game_7").get("mode"), chosen_gametypes[6].mode.name
        )
