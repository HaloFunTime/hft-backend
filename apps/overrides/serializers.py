import uuid

from rest_framework import serializers


def validate_uuid(value):
    """
    Validate that a string represents a UUID.
    """
    try:
        uuid.UUID(str(value))
        return value
    except ValueError:
        raise serializers.ValidationError("Only a valid UUID string is allowed.")
