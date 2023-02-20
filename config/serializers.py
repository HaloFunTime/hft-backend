from rest_framework import serializers


# Designed to match payload defined in config/urls.py by method `root_exception_handler`
class StandardErrorSerializer(serializers.Serializer):
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    details = serializers.DictField()
