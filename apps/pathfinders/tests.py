from django.contrib.auth.models import User
from django.test import TestCase


class PathfinderUtilsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )

    def test_get_illuminated_qualified(self):
        # TODO: Test Illuminated logic after implementation
        pass

    def test_get_dynamo_qualified(self):
        # TODO: Test Dynamo logic after implementation
        pass
