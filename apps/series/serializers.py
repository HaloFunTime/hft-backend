from rest_framework import serializers

from apps.series.models import SeriesRuleset


class SeriesRulesetSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesRuleset
        fields = ["name", "id"]


class SeriesBo3Serializer(serializers.Serializer):
    title = serializers.CharField()
    subtitle = serializers.CharField()
    game_1 = serializers.CharField()
    game_2 = serializers.CharField()
    game_3 = serializers.CharField()


class SeriesBo5Serializer(SeriesBo3Serializer):
    game_4 = serializers.CharField()
    game_5 = serializers.CharField()


class SeriesBo7Serializer(SeriesBo5Serializer):
    game_6 = serializers.CharField()
    game_7 = serializers.CharField()


class SeriesErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
