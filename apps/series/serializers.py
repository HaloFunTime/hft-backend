from rest_framework import serializers

from apps.series.models import SeriesRuleset


class SeriesRulesetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesRuleset
        fields = ["name", "id"]


class SeriesGameSerializer(serializers.Serializer):
    map = serializers.CharField()
    map_file_id = serializers.CharField()
    mode = serializers.CharField()
    mode_file_id = serializers.CharField()


class SeriesBo3Serializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField()
    game_1 = SeriesGameSerializer()
    game_2 = SeriesGameSerializer()
    game_3 = SeriesGameSerializer()


class SeriesBo5Serializer(SeriesBo3Serializer):
    game_4 = SeriesGameSerializer()
    game_5 = SeriesGameSerializer()


class SeriesBo7Serializer(SeriesBo5Serializer):
    game_6 = SeriesGameSerializer()
    game_7 = SeriesGameSerializer()


class SeriesErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
