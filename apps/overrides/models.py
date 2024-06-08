import uuid

from django.conf import settings
from django.db import models
from rest_framework.authentication import TokenAuthentication


class BaseWithoutPrimaryKey(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.RESTRICT, related_name="+"
    )

    class Meta:
        abstract = True


class Base(BaseWithoutPrimaryKey):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class BearerAuthentication(TokenAuthentication):
    keyword = "Bearer"
