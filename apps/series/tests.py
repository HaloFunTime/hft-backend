from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from apps.series.models import SeriesRuleset


class SeriesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test", email="test@test.com", password="test"
        )
        token, created = Token.objects.get_or_create(user=self.user)
        self.client = APIClient(HTTP_AUTHORIZATION="Bearer " + token.key)

    def test_series_success(self):
        # Empty SeriesRuleset table returns empty array
        response = self.client.get("/series/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

        # SeriesRuleset table with one entry returns it
        test_ruleset_1 = SeriesRuleset(id="test", name="test", creator=self.user)
        test_ruleset_1.save()
        response = self.client.get("/series/")
        self.assertEqual(
            response.data, [{"name": test_ruleset_1.name, "id": test_ruleset_1.id}]
        )

        # SeriesRuleset table with two entries returns both, ordered by name
        test_ruleset_2 = SeriesRuleset(id="another", name="another", creator=self.user)
        test_ruleset_2.save()
        response = self.client.get("/series/")
        self.assertEqual(
            response.data,
            [
                {"name": test_ruleset_2.name, "id": test_ruleset_2.id},
                {"name": test_ruleset_1.name, "id": test_ruleset_1.id},
            ],
        )
