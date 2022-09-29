import itertools
import logging
import random
import time

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.series.exceptions import (
    SeriesBuildImpossibleException,
    SeriesBuildUnsupportedException,
)
from apps.series.models import SeriesGametype, SeriesRuleset
from apps.series.serializers import (
    SeriesBo3Serializer,
    SeriesBo5Serializer,
    SeriesBo7Serializer,
    SeriesErrorSerializer,
    SeriesRulesetSerializer,
)

logger = logging.getLogger(__name__)


def build_series(ruleset: SeriesRuleset, x: int) -> list[SeriesGametype]:
    """
    Returns a list of SeriesGametype records, ordered appropriately for a best of X series.
    """
    start = time.perf_counter()
    # 1) Validate that x is 3, 5, or 7
    if x != 3 and x != 5 and x != 7:
        raise SeriesBuildUnsupportedException()

    # 2) Get all gametypes related to the ruleset and shuffle them
    ruleset_gametypes = list(
        SeriesGametype.objects.select_related("ruleset", "map", "mode").filter(
            ruleset=ruleset
        )
    )
    random.shuffle(ruleset_gametypes)
    if len(ruleset_gametypes) < x:
        raise SeriesBuildImpossibleException()

    # 3) Compute all possible combinations of x gametype selections
    combinations = list(itertools.combinations(ruleset_gametypes, x))
    logger.info(
        f"Bo{x}: {len(combinations)} total series combinations for ruleset '{ruleset.id}'"
    )

    # 4) Filter the list down to all combinations matching the ruleset's restrictions
    valid_combinations = []
    for combination in combinations:
        # Enforce featured mode constraints
        if ruleset.featured_mode is not None:
            # There must be exactly y occurrences of the featured mode in a best of x series
            y = {3: 1, 5: 2, 7: 3}.get(x)
            featured_mode_occurrences = 0
            for gametype in combination:
                if gametype.mode == ruleset.featured_mode:
                    featured_mode_occurrences += 1
            if featured_mode_occurrences != y:
                continue
        # Detect map repeats
        map_repeats_allowed = {
            3: ruleset.allow_bo3_map_repeats,
            5: ruleset.allow_bo5_map_repeats,
            7: ruleset.allow_bo7_map_repeats,
        }.get(x)
        if not map_repeats_allowed:
            repeat_detected = False
            for gametype1, gametype2 in itertools.combinations(combination, 2):
                if gametype1.map == gametype2.map:
                    repeat_detected = True
                    break
            if repeat_detected:
                continue
        # Detect mode repeats
        mode_repeats_allowed = {
            3: ruleset.allow_bo3_mode_repeats,
            5: ruleset.allow_bo5_mode_repeats,
            7: ruleset.allow_bo7_mode_repeats,
        }.get(x)
        if not mode_repeats_allowed:
            repeat_detected = False
            for gametype1, gametype2 in itertools.combinations(combination, 2):
                if gametype1.mode == gametype2.mode:
                    repeat_detected = (
                        True
                        if not bool(ruleset.featured_mode)
                        else gametype1.mode != ruleset.featured_mode
                    )
                    if repeat_detected:
                        break
            if repeat_detected:
                continue
        valid_combinations.append(combination)
    if len(valid_combinations) == 0:
        raise SeriesBuildImpossibleException()
    logger.info(
        f"Bo{x}: {len(valid_combinations)} valid series combinations for ruleset '{ruleset.id}'"
    )

    # 5) Slice and dice the valid combinations by uniqueness counts to build a list of the most diverse combinations
    one_to_x_range = range(1, x + 1)
    valid_combinations_by_unique_map_count = {i: [] for i in one_to_x_range}
    valid_combinations_by_unique_mode_count = {i: [] for i in one_to_x_range}
    for combination in valid_combinations:
        unique_maps = set()
        unique_modes = set()
        for gametype in combination:
            unique_maps.add(gametype.map)
            unique_modes.add(gametype.mode)
        valid_combinations_by_unique_map_count[len(unique_maps)].append(combination)
        valid_combinations_by_unique_mode_count[len(unique_modes)].append(combination)
    unique_map_high_water_mark = 0
    unique_mode_high_water_mark = 0
    for i in one_to_x_range:
        if len(valid_combinations_by_unique_map_count[i]) > 0:
            unique_map_high_water_mark = i
        if len(valid_combinations_by_unique_mode_count[i]) > 0:
            unique_mode_high_water_mark = i
    diverse_map_combinations = set(
        valid_combinations_by_unique_map_count[unique_map_high_water_mark]
    )
    diverse_mode_combinations = set(
        valid_combinations_by_unique_mode_count[unique_mode_high_water_mark]
    )
    most_diverse_combinations = list(
        diverse_map_combinations.intersection(diverse_mode_combinations)
    )
    random.shuffle(most_diverse_combinations)

    # 6) Pop combinations from the list and evaluate their permutations for suitability
    ideal_permutation = None
    fallback_permutation = None
    while len(most_diverse_combinations) > 0:
        chosen_combination = list(most_diverse_combinations.pop())

        # 6a) Generate all valid permutations of the chosen combination; save a fallback
        permutations = list(itertools.permutations(chosen_combination, x))
        valid_permutations = []
        for permutation in permutations:
            # Enforce featured mode constraints
            if ruleset.featured_mode is not None:
                # Certain games must be the featured mode in a best of x
                games_that_must_be_featured_mode = {
                    3: [1],
                    5: [1, 4],
                    7: [1, 4, 6],
                }.get(x)
                permutation_violates_featured_mode_pattern = False
                for game in games_that_must_be_featured_mode:
                    if permutation[game].mode != ruleset.featured_mode:
                        permutation_violates_featured_mode_pattern = True
                        break
                if permutation_violates_featured_mode_pattern:
                    continue
            valid_permutations.append(permutation)
        fallback_permutation = random.choice(valid_permutations)
        # 6b) Generate ideal permutations from the valid permutations
        # NOTE: We define an "ideal" permutation as one where no map or mode is played twice consecutively
        ideal_permutations = []
        for valid_permutation in valid_permutations:
            # Evaluate the valid permutation for consecutive plays of the same map or mode
            has_consecutive_plays = False
            i = 1
            while i < len(valid_permutation):
                gametypeA = valid_permutation[i - 1]
                gametypeB = valid_permutation[i]
                if gametypeA.map == gametypeB.map or gametypeA.mode == gametypeB.mode:
                    has_consecutive_plays = True
                    break
                i += 1
            if not has_consecutive_plays:
                ideal_permutations.append(valid_permutation)
        # 6c) If we have any ideal permutations, choose one and break (otherwise try again with another combination)
        if len(ideal_permutations) != 0:
            ideal_permutation = random.choice(ideal_permutations)
            break
    chosen_permutation = (
        ideal_permutation if ideal_permutation is not None else fallback_permutation
    )
    end = time.perf_counter()
    logger.info(f"Bo{x}: Found series in {end - start:0.4f} seconds")
    return list(chosen_permutation)


def build_best_of_dict(
    ruleset: SeriesRuleset, chosen_gametypes: list[SeriesGametype]
) -> dict:
    best_of_dict = {
        "title": ruleset.name,
        "subtitle": f"Best of {len(chosen_gametypes)}",
    }
    for i in range(1, len(chosen_gametypes) + 1):
        gametype = chosen_gametypes[i - 1]
        best_of_dict[f"game_{i}"] = f"{gametype.mode.name} on {gametype.map.name}"
    return best_of_dict


class Series(APIView):
    @extend_schema(
        responses={
            200: SeriesRulesetSerializer(many=True),
        }
    )
    def get(self, request):
        """
        Retrieves a list of all available series rulesets.
        """
        series_rulesets = SeriesRuleset.objects.all().order_by("name")
        serializer = SeriesRulesetSerializer(series_rulesets, many=True)
        return Response(serializer.data)


class SeriesBo3(APIView):
    @extend_schema(
        responses={
            200: SeriesBo3Serializer,
            400: SeriesErrorSerializer,
            404: SeriesErrorSerializer,
            500: SeriesErrorSerializer,
        }
    )
    def get(self, request, **kwargs):
        """
        Retrieves a randomized best of 3 series for the given ruleset.
        """
        ruleset_id = kwargs.get("id", None)
        if not ruleset_id:
            serializer = SeriesErrorSerializer({"error": "Missing 'id' in URL"})
            return Response(serializer.data, status=400)
        try:
            ruleset = SeriesRuleset.objects.select_related("featured_mode").get(
                id=ruleset_id
            )
        except Exception:
            serializer = SeriesErrorSerializer(
                {"error": f"Could not retrieve '{ruleset_id}' series ruleset."}
            )
            return Response(serializer.data, status=404)
        try:
            gametypes = build_series(ruleset, 3)
            serializer = SeriesBo3Serializer(build_best_of_dict(ruleset, gametypes))
            return Response(serializer.data, status=200)
        except SeriesBuildImpossibleException:
            logger.debug(
                f"Series failure - Bo3 for ruleset '{ruleset.id}' cannot be built"
            )
            serializer = SeriesErrorSerializer(
                {
                    "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
                }
            )
            return Response(serializer.data, status=500)


class SeriesBo5(APIView):
    @extend_schema(
        responses={
            200: SeriesBo5Serializer,
            400: SeriesErrorSerializer,
            404: SeriesErrorSerializer,
            500: SeriesErrorSerializer,
        }
    )
    def get(self, request, **kwargs):
        """
        Retrieves a randomized best of 5 series for the given ruleset.
        """
        ruleset_id = kwargs.get("id", None)
        if not ruleset_id:
            serializer = SeriesErrorSerializer({"error": "Missing 'id' in URL"})
            return Response(serializer.data, status=400)
        try:
            ruleset = SeriesRuleset.objects.select_related("featured_mode").get(
                id=ruleset_id
            )
        except Exception:
            serializer = SeriesErrorSerializer(
                {"error": f"Could not retrieve '{ruleset_id}' series ruleset."}
            )
            return Response(serializer.data, status=404)
        try:
            gametypes = build_series(ruleset, 5)
            serializer = SeriesBo5Serializer(build_best_of_dict(ruleset, gametypes))
            return Response(serializer.data, status=200)
        except SeriesBuildImpossibleException:
            logger.debug(
                f"Series failure - Bo5 for ruleset '{ruleset.id}' cannot be built"
            )
            serializer = SeriesErrorSerializer(
                {
                    "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
                }
            )
            return Response(serializer.data, status=500)


class SeriesBo7(APIView):
    @extend_schema(
        responses={
            200: SeriesBo7Serializer,
            400: SeriesErrorSerializer,
            404: SeriesErrorSerializer,
            500: SeriesErrorSerializer,
        }
    )
    def get(self, request, **kwargs):
        """
        Retrieves a randomized best of 7 series for the given ruleset.
        """
        ruleset_id = kwargs.get("id", None)
        if not ruleset_id:
            serializer = SeriesErrorSerializer({"error": "Missing 'id' in URL"})
            return Response(serializer.data, status=400)
        try:
            ruleset = SeriesRuleset.objects.select_related("featured_mode").get(
                id=ruleset_id
            )
        except Exception:
            serializer = SeriesErrorSerializer(
                {"error": f"Could not retrieve '{ruleset_id}' series ruleset."}
            )
            return Response(serializer.data, status=404)
        try:
            gametypes = build_series(ruleset, 7)
            serializer = SeriesBo7Serializer(build_best_of_dict(ruleset, gametypes))
            return Response(serializer.data, status=200)
        except SeriesBuildImpossibleException:
            logger.debug(
                f"Series failure - Bo7 for ruleset '{ruleset.id}' cannot be built"
            )
            serializer = SeriesErrorSerializer(
                {
                    "error": "Cannot build series. Add more gametypes or loosen the ruleset restrictions."
                }
            )
            return Response(serializer.data, status=500)
