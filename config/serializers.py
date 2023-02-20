from rest_framework import serializers


# Designed to match payload defined in config/urls.py by method `root_exception_handler`
class ErrorSerializer(serializers.Serializer):
    status_code = serializers.IntegerField()
    message = serializers.CharField()
    details = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField())
    )


# Designed to match payload defined in config/urls.py by method `root_exception_handler`
class StandardErrorSerializer(serializers.Serializer):
    error = ErrorSerializer()
