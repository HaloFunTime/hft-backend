from rest_framework import serializers

from apps.series.models import SeriesRuleset


class SeriesRulesetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesRuleset
        fields = ["name", "id"]


class SeriesGameSerializer(serializers.Serializer):
    map = serializers.CharField()
    mapFileId = serializers.CharField()
    mode = serializers.CharField()
    modeFileId = serializers.CharField()


class SeriesBo3Serializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField()
    game1 = SeriesGameSerializer()
    game2 = SeriesGameSerializer()
    game3 = SeriesGameSerializer()


class SeriesBo5Serializer(SeriesBo3Serializer):
    game4 = SeriesGameSerializer()
    game5 = SeriesGameSerializer()


class SeriesBo7Serializer(SeriesBo5Serializer):
    game6 = SeriesGameSerializer()
    game7 = SeriesGameSerializer()


class SeriesErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
