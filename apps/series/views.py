import logging

from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.series.exceptions import SeriesBuildImpossibleException
from apps.series.models import SeriesRuleset
from apps.series.serializers import (
    SeriesBo3Serializer,
    SeriesBo5Serializer,
    SeriesBo7Serializer,
    SeriesErrorSerializer,
    SeriesRulesetSerializer,
)
from apps.series.utils import build_best_of_dict, build_series

logger = logging.getLogger(__name__)


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
